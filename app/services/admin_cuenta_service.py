from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.datetime_utils import ahora_utc
from app.models.profesional import Profesional
from app.models.evento_suscripcion import EventoSuscripcion
from app.models.usuario import Usuario
from app.repositories.admin_cuenta_repository import (
    listar_cuentas_admin,
    listar_profesionales_de_cuentas,
    listar_propietarios_de_cuentas,
    obtener_cuenta_admin_por_id,
    obtener_resumen_cuentas_admin,
    obtener_suscripcion_admin,
    listar_eventos_suscripcion,
)
from app.schemas.admin_cuenta import (
    AdminCuentaDatosRespuesta,
    AdminCuentaDetalleRespuesta,
    AdminCuentaItemRespuesta,
    AdminCuentasPaginaRespuesta,
    AdminCuentasResumenRespuesta,
    AdminMiembroCuentaRespuesta,
    AdminProfesionalCuentaRespuesta,
    AdminProfesionalPrincipalRespuesta,
    AdminSuscripcionDetalleRespuesta,
    AdminEventoSuscripcionRespuesta,
)
from app.services.cuenta_service import dias_trial_restantes, estado_efectivo
from app.core.datetime_utils import desde_base_utc


def _profesional_principal(
    profesionales: list[Profesional],
    propietario_usuario_id: int | None,
) -> Profesional | None:
    if propietario_usuario_id is not None:
        asociado = next(
            (item for item in profesionales if item.usuario_id == propietario_usuario_id),
            None,
        )
        if asociado is not None:
            return asociado
    return profesionales[0] if profesionales else None


def _profesional_principal_respuesta(
    profesional: Profesional | None,
) -> AdminProfesionalPrincipalRespuesta | None:
    if profesional is None:
        return None
    return AdminProfesionalPrincipalRespuesta(
        profesional_id=profesional.id,
        nombre=profesional.nombre,
        apellido=profesional.apellido,
        matricula=profesional.matricula,
        email=profesional.email,
    )


def obtener_cuentas_admin(
    db: Session,
    *,
    q: str | None,
    estado: str | None,
    plan: str | None,
    created_from: date | None,
    created_to: date | None,
    offset: int,
    limit: int,
) -> AdminCuentasPaginaRespuesta:
    if created_from and created_to and created_from > created_to:
        raise HTTPException(status_code=400, detail="El rango de fechas no es válido.")
    termino = q.strip() if q else None
    ahora = ahora_utc()
    filas, total = listar_cuentas_admin(
        db, q=termino or None, estado=estado, plan=plan,
        created_from=created_from, created_to=created_to,
        offset=offset, limit=limit, ahora=ahora,
    )
    cuenta_ids = [cuenta.id for cuenta, _, _, _ in filas]
    profesionales_por_cuenta: dict[int, list[Profesional]] = {}
    for profesional in listar_profesionales_de_cuentas(db, cuenta_ids):
        profesionales_por_cuenta.setdefault(profesional.cuenta_id, []).append(profesional)
    propietario_por_cuenta = {}
    for membresia in listar_propietarios_de_cuentas(db, cuenta_ids):
        propietario_por_cuenta.setdefault(membresia.cuenta_id, membresia.usuario_id)

    items = []
    for cuenta, suscripcion, profesionales_count, miembros_count in filas:
        principal = _profesional_principal(
            profesionales_por_cuenta.get(cuenta.id, []),
            propietario_por_cuenta.get(cuenta.id),
        )
        items.append(AdminCuentaItemRespuesta(
            cuenta_id=cuenta.id,
            nombre=cuenta.nombre,
            tipo=cuenta.tipo,
            plan=suscripcion.plan_code if suscripcion else None,
            estado=estado_efectivo(suscripcion, ahora) if suscripcion else "sin_suscripcion",
            created_at=cuenta.created_at,
            trial_ends_at=suscripcion.trial_ends_at if suscripcion else None,
            profesionales_count=int(profesionales_count),
            miembros_count=int(miembros_count),
            profesional_principal=_profesional_principal_respuesta(principal),
        ))
    return AdminCuentasPaginaRespuesta(
        items=items, total=total, offset=offset, limit=limit,
    )


def obtener_resumen_admin(db: Session) -> AdminCuentasResumenRespuesta:
    valores = obtener_resumen_cuentas_admin(db, ahora_utc())
    return AdminCuentasResumenRespuesta(
        cuentas_totales=int(valores[0]),
        trials_activos=int(valores[1]),
        suscripciones_activas=int(valores[2]),
        trials_finalizados=int(valores[3]),
        altas_ultimos_30_dias=int(valores[4]),
    )


def obtener_detalle_cuenta_admin(db: Session, cuenta_id: int) -> AdminCuentaDetalleRespuesta:
    cuenta = obtener_cuenta_admin_por_id(db, cuenta_id)
    if cuenta is None:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada.")
    ahora = ahora_utc()
    suscripcion = cuenta.suscripcion
    suscripcion_respuesta = None
    if suscripcion is not None:
        efectivo = estado_efectivo(suscripcion, ahora)
        suscripcion_respuesta = AdminSuscripcionDetalleRespuesta(
            plan=suscripcion.plan_code,
            estado=efectivo,
            estado_persistido=suscripcion.status if suscripcion.status != efectivo else None,
            trial_started_at=suscripcion.trial_started_at,
            trial_ends_at=suscripcion.trial_ends_at,
            trial_days_remaining=dias_trial_restantes(suscripcion, ahora),
        )
    return AdminCuentaDetalleRespuesta(
        cuenta=AdminCuentaDatosRespuesta(
            id=cuenta.id,
            nombre=cuenta.nombre,
            tipo=cuenta.tipo,
            created_at=cuenta.created_at,
            updated_at=cuenta.updated_at,
        ),
        suscripcion=suscripcion_respuesta,
        miembros=[
            AdminMiembroCuentaRespuesta(
                usuario_id=item.usuario_id,
                nombre=item.usuario.nombre,
                email=item.usuario.email,
                rol_cuenta=item.rol_cuenta,
                activo=item.usuario.activo,
                miembro_desde=item.created_at,
            )
            for item in sorted(cuenta.membresias, key=lambda item: (item.created_at, item.usuario_id))
        ],
        profesionales=[
            AdminProfesionalCuentaRespuesta(
                id=item.id,
                nombre=item.nombre,
                apellido=item.apellido,
                matricula=item.matricula,
                email=item.email,
                activo=item.activo,
            )
            for item in sorted(cuenta.profesionales, key=lambda item: item.id)
        ],
    )


def _suscripcion_o_error(db: Session, cuenta_id: int):
    cuenta = obtener_cuenta_admin_por_id(db, cuenta_id)
    if cuenta is None:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada.")
    suscripcion = obtener_suscripcion_admin(db, cuenta_id)
    if suscripcion is None:
        raise HTTPException(status_code=409, detail="La cuenta no tiene una suscripción asociada.")
    return suscripcion


def _motivo(valor: str | None) -> str | None:
    limpio = valor.strip() if valor else None
    if limpio and len(limpio) > 500:
        raise HTTPException(status_code=422, detail="El motivo no puede superar 500 caracteres.")
    return limpio or None


def _registrar(db, suscripcion, actor, accion, anterior, nuevo, *, plan_anterior=None, plan_nuevo=None, motivo=None):
    db.add(EventoSuscripcion(
        cuenta_id=suscripcion.cuenta_id, suscripcion_id=suscripcion.id,
        actor_usuario_id=actor.id, actor_tipo="usuario", accion=accion,
        estado_anterior=anterior, estado_nuevo=nuevo,
        plan_anterior=plan_anterior, plan_nuevo=plan_nuevo, motivo=_motivo(motivo),
    ))


def _cambiar_estado(db: Session, cuenta_id: int, actor: Usuario, *, accion: str, permitidos: set[str], nuevo: str, motivo: str | None):
    suscripcion = _suscripcion_o_error(db, cuenta_id)
    anterior = estado_efectivo(suscripcion)
    if anterior not in permitidos:
        raise HTTPException(status_code=409, detail=f"No se puede ejecutar esta acción desde el estado {anterior}.")
    suscripcion.status = nuevo
    _registrar(db, suscripcion, actor, accion, anterior, nuevo, motivo=motivo)
    db.commit()
    return obtener_detalle_cuenta_admin(db, cuenta_id)


def activar_suscripcion_admin(db: Session, cuenta_id: int, actor: Usuario, motivo: str | None):
    return _cambiar_estado(db, cuenta_id, actor, accion="activar", permitidos={"trial", "expired", "past_due", "cancelled"}, nuevo="active", motivo=motivo)


def reactivar_suscripcion_admin(db: Session, cuenta_id: int, actor: Usuario, motivo: str | None):
    return _cambiar_estado(db, cuenta_id, actor, accion="reactivar", permitidos={"past_due", "cancelled"}, nuevo="active", motivo=motivo)


def marcar_pago_pendiente_admin(db: Session, cuenta_id: int, actor: Usuario, motivo: str | None):
    return _cambiar_estado(db, cuenta_id, actor, accion="marcar_pago_pendiente", permitidos={"active"}, nuevo="past_due", motivo=motivo)


def cancelar_suscripcion_admin(db: Session, cuenta_id: int, actor: Usuario, motivo: str | None):
    return _cambiar_estado(db, cuenta_id, actor, accion="cancelar", permitidos={"trial", "expired", "active", "past_due"}, nuevo="cancelled", motivo=motivo)


def extender_trial_admin(db: Session, cuenta_id: int, actor: Usuario, dias: int, motivo: str | None):
    suscripcion = _suscripcion_o_error(db, cuenta_id)
    ahora = ahora_utc()
    anterior = estado_efectivo(suscripcion, ahora)
    if anterior not in {"trial", "expired"}:
        raise HTTPException(status_code=409, detail="Solo se puede extender una prueba activa o vencida.")
    base = max(ahora, desde_base_utc(suscripcion.trial_ends_at)) if suscripcion.trial_ends_at else ahora
    suscripcion.status = "trial"
    suscripcion.trial_started_at = suscripcion.trial_started_at or ahora
    suscripcion.trial_ends_at = base + timedelta(days=dias)
    _registrar(db, suscripcion, actor, "extender_trial", anterior, "trial", motivo=motivo)
    db.commit()
    return obtener_detalle_cuenta_admin(db, cuenta_id)


def cambiar_plan_admin(db: Session, cuenta_id: int, actor: Usuario, plan: str, motivo: str | None):
    suscripcion = _suscripcion_o_error(db, cuenta_id)
    anterior = suscripcion.plan_code
    if anterior == plan:
        raise HTTPException(status_code=409, detail="La suscripción ya tiene ese plan.")
    estado = estado_efectivo(suscripcion)
    suscripcion.plan_code = plan
    _registrar(db, suscripcion, actor, "cambiar_plan", estado, estado, plan_anterior=anterior, plan_nuevo=plan, motivo=motivo)
    db.commit()
    return obtener_detalle_cuenta_admin(db, cuenta_id)


def obtener_historial_admin(db: Session, cuenta_id: int) -> list[AdminEventoSuscripcionRespuesta]:
    if obtener_cuenta_admin_por_id(db, cuenta_id) is None:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada.")
    return [AdminEventoSuscripcionRespuesta(
        id=e.id, actor_usuario_id=e.actor_usuario_id,
        actor_nombre=e.actor_usuario.nombre if e.actor_usuario else None,
        actor_tipo=e.actor_tipo, accion=e.accion,
        estado_anterior=e.estado_anterior, estado_nuevo=e.estado_nuevo,
        plan_anterior=e.plan_anterior, plan_nuevo=e.plan_nuevo,
        motivo=e.motivo, created_at=e.created_at,
    ) for e in listar_eventos_suscripcion(db, cuenta_id)]
