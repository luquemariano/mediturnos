from datetime import datetime, timedelta
import hashlib
import secrets

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.datetime_utils import ahora_utc, desde_base_utc
from app.models.consultorio_profesional import ConsultorioProfesional
from app.models.invitacion_consultorio import InvitacionConsultorio
from app.models.ocurrencia_modulo import OcurrenciaModulo
from app.models.profesional import Profesional
from app.models.regla_recurrencia_modulo import ReglaRecurrenciaModulo
from app.models.serie_modulo import SerieModulo
from app.models.usuario import Usuario
from app.repositories import consultorio_invitacion_repository as repository
from app.repositories.consultorio_modulo_repository import bloquear_sala, crear_regla
from app.schemas.consultorio_invitacion import InvitacionCrear
from app.services.consultorio_modulo_service import _crear_ocurrencias_regla, _validar_regla_sin_solape, _tz
from app.services.email_service import TransactionalEmail, obtener_email_provider


TOKEN_INVALIDO = "La invitación no está disponible. Revisá que el enlace sea válido y que tu correo esté verificado."


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _admin(db: Session, user: Usuario, clinic_id: int):
    from app.repositories.consultorio_repository import buscar_consultorio_administrado
    clinic = buscar_consultorio_administrado(db, clinic_id, user.id)
    if clinic is None:
        raise HTTPException(404, "No se encontró el consultorio.")
    return clinic


def _count_slots(db: Session, invite_id: int) -> int:
    return int(db.scalar(select(func.count(OcurrenciaModulo.id)).where(OcurrenciaModulo.invitacion_id == invite_id, OcurrenciaModulo.estado == "activa")) or 0)


def _response(invite: InvitacionConsultorio) -> dict:
    return {
        "id": invite.id,
        "email": invite.email_normalizado,
        "nombre_visible": invite.nombre_visible,
        "estado": invite.estado,
        "vence_en": invite.vence_en,
        "modulos_reservados": 0,
    }


def _expire_old(db: Session, clinic_id: int, now: datetime) -> None:
    stale = db.scalars(select(InvitacionConsultorio).where(
        InvitacionConsultorio.consultorio_id == clinic_id,
        InvitacionConsultorio.estado.in_(("pendiente", "preparacion")),
        InvitacionConsultorio.vence_en <= now,
    ).with_for_update()).all()
    for invite in stale:
        invite.estado = "expirada"
        invite.token_hash = None
        db.query(OcurrenciaModulo).filter(OcurrenciaModulo.invitacion_id == invite.id, OcurrenciaModulo.estado == "activa").update({"estado": "cancelada"}, synchronize_session=False)
        series_ids = select(SerieModulo.id).where(SerieModulo.invitacion_id == invite.id)
        db.query(ReglaRecurrenciaModulo).filter(ReglaRecurrenciaModulo.serie_id.in_(series_ids), ReglaRecurrenciaModulo.estado == "activa").update({"estado": "cancelada"}, synchronize_session=False)


def _assert_seat(db: Session, clinic, now: datetime, *, exclude_invite_id: int | None = None) -> None:
    occupied = len(repository.contar_profesionales_activos(db, clinic.id)) + repository.contar_invitaciones_pendientes(db, clinic.id, now, exclude_invite_id)
    if occupied >= clinic.cupo_profesionales:
        raise HTTPException(409, "El consultorio alcanzó el cupo de integrantes.")


def crear_invitacion(db: Session, user: Usuario, clinic_id: int, datos: InvitacionCrear) -> dict:
    _admin(db, user, clinic_id)
    locked = repository.bloquear_consultorio(db, clinic_id)
    if locked is None or locked.estado != "activo":
        raise HTTPException(409, "El consultorio no está disponible.")
    now = ahora_utc()
    _expire_old(db, clinic_id, now)
    _assert_seat(db, locked, now)
    email = str(datos.email).strip().lower()
    invite = InvitacionConsultorio(
        consultorio_id=clinic_id, email_normalizado=email,
        nombre_visible=datos.nombre_visible.strip() if datos.nombre_visible else None,
        estado="preparacion", invitante_usuario_id=user.id,
        vence_en=now + timedelta(days=locked.invitacion_expiracion_dias),
    )
    db.add(invite)
    try:
        db.flush()
        for slot in datos.modulos:
            sala = bloquear_sala(db, clinic_id, slot.sala_id)
            if sala is None:
                raise HTTPException(404, "No se encontró la sala activa.")
            duration = slot.duracion_minutos or locked.duracion_modulo_minutos
            rule_data = {
                "dia_semana": slot.dia_semana,
                "hora_inicio": slot.hora_inicio.replace(tzinfo=None),
                "duracion_minutos": duration,
                "vigente_desde": slot.vigente_desde,
                "vigente_hasta": slot.vigente_hasta,
            }
            if slot.vigente_desde < now.astimezone(_tz(locked.zona_horaria)).date():
                raise HTTPException(422, "La recurrencia no puede comenzar en una fecha pasada.")
            _validar_regla_sin_solape(db, sala.id, rule_data)
            series = SerieModulo(consultorio_id=clinic_id, sala_id=sala.id, profesional_id=None, invitacion_id=invite.id, creado_por_usuario_id=user.id)
            db.add(series)
            db.flush()
            rule = crear_regla(db, series.id, version=1, **rule_data, zona_horaria=locked.zona_horaria)
            local_today = now.astimezone(_tz(locked.zona_horaria)).date()
            _crear_ocurrencias_regla(db, locked, rule, local_today, local_today + timedelta(days=locked.horizonte_materializacion_dias - 1), user.id)
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        if getattr(getattr(exc.orig, "diag", None), "constraint_name", None) == "ex_consultorio_sala_intervalo_activo":
            raise HTTPException(409, "El horario de la sala ya no está disponible.") from None
        raise HTTPException(409, "No se pudo reservar el cupo o los módulos solicitados.") from None
    db.refresh(invite)
    result = _response(invite)
    result["modulos_reservados"] = _count_slots(db, invite.id)
    return result


def _send(invite: InvitacionConsultorio, token: str) -> None:
    from urllib.parse import quote
    url = f"{settings.frontend_url.rstrip('/')}/invitacion-consultorio#token={quote(token)}"
    name = invite.nombre_visible or "Hola"
    body = f"{name}, te invitaron a sumarte a un consultorio en Turnelia.\n\nAbrí este enlace e iniciá sesión o registrate para aceptar: {url}\n\nEl enlace vence según lo indicado en la invitación."
    try:
        obtener_email_provider().enviar(TransactionalEmail(invite.email_normalizado, "Invitación a un consultorio — Turnelia", body, body))
    except Exception as exc:
        raise HTTPException(503, "No se pudo entregar la invitación. Podés volver a enviarla desde el panel.") from exc


def enviar_invitacion(db: Session, user: Usuario, clinic_id: int, invite_id: int, reenvio: bool = False) -> dict:
    _admin(db, user, clinic_id)
    clinic = repository.bloquear_consultorio(db, clinic_id)
    invite = repository.bloquear_invitacion(db, invite_id, clinic_id)
    now = ahora_utc()
    if clinic is None or invite is None:
        raise HTTPException(404, "No se encontró la invitación.")
    if clinic.estado != "activo":
        raise HTTPException(409, "El consultorio está suspendido.")
    if invite.estado in ("preparacion", "pendiente") and invite.vence_en and desde_base_utc(invite.vence_en) <= now:
        _expire_old(db, clinic_id, now)
        db.commit()
        raise HTTPException(409, "La invitación venció; prepará una nueva invitación.")
    if invite.estado not in ("preparacion", "pendiente"):
        raise HTTPException(409, "La invitación no está disponible para envío.")
    if reenvio:
        _expire_old(db, clinic_id, now)
    token = secrets.token_urlsafe(32)
    invite.token_hash = _hash(token)
    invite.estado = "pendiente"
    invite.invitante_usuario_id = user.id
    invite.vence_en = now + timedelta(days=clinic.invitacion_expiracion_dias)
    db.commit()
    _send(invite, token)
    return {"id": invite.id, "estado": invite.estado, "vence_en": invite.vence_en, "mensaje": "Invitación enviada."}


def listar_invitaciones(db: Session, user: Usuario, clinic_id: int) -> list[dict]:
    _admin(db, user, clinic_id)
    repository.bloquear_consultorio(db, clinic_id)
    _expire_old(db, clinic_id, ahora_utc())
    db.commit()
    invites = repository.listar(db, clinic_id)
    rows = []
    for invite in invites:
        rows.append({
            "id": invite.id, "email": invite.email_normalizado,
            "nombre_visible": invite.nombre_visible, "estado": invite.estado,
            "vence_en": invite.vence_en,
            "modulos_reservados": _count_slots(db, invite.id),
        })
    return rows


def revocar_invitacion(db: Session, user: Usuario, clinic_id: int, invite_id: int) -> dict:
    _admin(db, user, clinic_id)
    repository.bloquear_consultorio(db, clinic_id)
    invite = repository.bloquear_invitacion(db, invite_id, clinic_id)
    if invite is None:
        raise HTTPException(404, "No se encontró la invitación.")
    if invite.estado not in ("preparacion", "pendiente"):
        raise HTTPException(409, "La invitación ya no se puede revocar.")
    invite.estado = "revocada"
    invite.revocada_en = ahora_utc()
    invite.token_hash = None
    db.query(OcurrenciaModulo).filter(OcurrenciaModulo.invitacion_id == invite.id, OcurrenciaModulo.estado == "activa").update({"estado": "cancelada"}, synchronize_session=False)
    series_ids = select(SerieModulo.id).where(SerieModulo.invitacion_id == invite.id)
    db.query(ReglaRecurrenciaModulo).filter(ReglaRecurrenciaModulo.serie_id.in_(series_ids), ReglaRecurrenciaModulo.estado == "activa").update({"estado": "cancelada"}, synchronize_session=False)
    db.commit()
    return {"id": invite.id, "estado": invite.estado}


def aceptar_invitacion(db: Session, user: Usuario, token: str) -> dict:
    # Discover only the clinic id first; all writers then lock clinic before invitation.
    invite_id = db.scalar(select(InvitacionConsultorio.id).where(InvitacionConsultorio.token_hash == _hash(token)))
    if invite_id is None:
        raise HTTPException(400, TOKEN_INVALIDO)
    clinic_id = db.scalar(select(InvitacionConsultorio.consultorio_id).where(InvitacionConsultorio.id == invite_id))
    clinic = repository.bloquear_consultorio(db, clinic_id)
    invite = repository.bloquear_invitacion(db, invite_id, clinic_id)
    now = ahora_utc()
    if clinic is None or clinic.estado != "activo" or invite is None:
        raise HTTPException(400, TOKEN_INVALIDO)
    if invite.estado == "aceptada" and invite.aceptada_por_usuario_id == user.id:
        return {"mensaje": "La invitación ya fue aceptada.", "consultorio_id": clinic_id, "profesional_vinculado": True}
    if invite.estado == "pendiente" and invite.vence_en is not None and desde_base_utc(invite.vence_en) <= now:
        _expire_old(db, clinic_id, now)
        db.commit()
        raise HTTPException(400, TOKEN_INVALIDO)
    if invite.estado != "pendiente" or invite.vence_en is None or invite.token_hash != _hash(token):
        raise HTTPException(400, TOKEN_INVALIDO)
    email = (user.email or "").strip().lower()
    if user.rol != "profesional" or not user.email_verificado or email != invite.email_normalizado:
        raise HTTPException(400, TOKEN_INVALIDO)
    professional = db.scalar(select(Profesional).where(Profesional.usuario_id == user.id, Profesional.activo.is_(True)).with_for_update())
    if professional is None:
        # Normal public registration remains independent; don't create a profile or account here.
        raise HTTPException(409, "Completá el alta profesional y verificá tu correo antes de aceptar.")
    _expire_old(db, clinic_id, now)
    _assert_seat(db, clinic, now, exclude_invite_id=invite.id)
    existing = db.scalar(select(ConsultorioProfesional).where(
        ConsultorioProfesional.consultorio_id == clinic_id,
        ConsultorioProfesional.profesional_id == professional.id,
    ).with_for_update())
    if existing is None:
        db.add(ConsultorioProfesional(consultorio_id=clinic_id, profesional_id=professional.id, estado="activo"))
    elif existing.estado not in ("activo", "preparatorio"):
        raise HTTPException(409, "El vínculo profesional no puede activarse.")
    else:
        existing.estado = "activo"
    db.query(SerieModulo).filter(SerieModulo.invitacion_id == invite.id).update({"profesional_id": professional.id, "invitacion_id": None}, synchronize_session=False)
    db.query(OcurrenciaModulo).filter(OcurrenciaModulo.invitacion_id == invite.id).update({"profesional_id": professional.id, "invitacion_id": None}, synchronize_session=False)
    invite.estado = "aceptada"
    invite.aceptada_por_usuario_id = user.id
    invite.aceptada_por_profesional_id = professional.id
    invite.vence_en = None
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "La invitación no pudo aplicarse por un conflicto de integridad.") from None
    return {"mensaje": "Invitación aceptada.", "consultorio_id": clinic_id, "profesional_vinculado": True}
