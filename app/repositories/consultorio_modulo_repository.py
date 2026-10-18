from datetime import date, datetime

from sqlalchemy import and_, exists, func, or_, select, update
from sqlalchemy.orm import Session, joinedload

from app.models.consultorio import Consultorio
from app.models.consultorio_profesional import ConsultorioProfesional
from app.models.invitacion_consultorio import InvitacionConsultorio
from app.models.ocurrencia_modulo import OcurrenciaModulo
from app.models.profesional import Profesional
from app.models.regla_recurrencia_modulo import ReglaRecurrenciaModulo
from app.models.sala import Sala
from app.models.serie_modulo import SerieModulo
from app.models.turno import Turno


ESTADOS_TURNO_ACTIVOS = ("reservado", "confirmado")


def bloquear_sala(db: Session, consultorio_id: int, sala_id: int) -> Sala | None:
    return (
        db.query(Sala)
        .filter(Sala.consultorio_id == consultorio_id, Sala.id == sala_id, Sala.estado == "activa")
        .with_for_update()
        .one_or_none()
    )


def bloquear_salas(db: Session, consultorio_id: int, sala_ids: set[int]) -> list[Sala]:
    return (
        db.query(Sala)
        .filter(Sala.consultorio_id == consultorio_id, Sala.id.in_(sala_ids), Sala.estado == "activa")
        .order_by(Sala.id)
        .with_for_update()
        .all()
    )


def profesional_vinculado_preparado(db: Session, consultorio_id: int, profesional_id: int) -> bool:
    return (
        db.query(ConsultorioProfesional.id)
        .join(Profesional, Profesional.id == ConsultorioProfesional.profesional_id)
        .filter(
            ConsultorioProfesional.consultorio_id == consultorio_id,
            ConsultorioProfesional.profesional_id == profesional_id,
            ConsultorioProfesional.estado.in_(("preparatorio", "activo")),
            Profesional.activo.is_(True),
        )
        .first()
        is not None
    )


def profesional_tiene_vinculo_activo(db: Session, profesional_id: int) -> bool:
    return (
        db.query(ConsultorioProfesional.id)
        .filter(
            ConsultorioProfesional.profesional_id == profesional_id,
            ConsultorioProfesional.estado == "activo",
        )
        .first()
        is not None
    )


def profesional_vinculado(db: Session, profesional_id: int) -> bool:
    return (
        db.query(ConsultorioProfesional.id)
        .filter(
            ConsultorioProfesional.profesional_id == profesional_id,
            ConsultorioProfesional.estado.in_(("preparatorio", "activo")),
        )
        .first()
        is not None
    )


def consultorio_de_regla(db: Session, regla_id: int) -> tuple[ReglaRecurrenciaModulo, SerieModulo, Consultorio] | None:
    fila = (
        db.query(ReglaRecurrenciaModulo, SerieModulo, Consultorio)
        .join(SerieModulo, ReglaRecurrenciaModulo.serie_id == SerieModulo.id)
        .join(Consultorio, Consultorio.id == SerieModulo.consultorio_id)
        .filter(ReglaRecurrenciaModulo.id == regla_id)
        .one_or_none()
    )
    return fila


def listar_reglas_consultorio(db: Session, consultorio_id: int, ahora: datetime) -> list[ReglaRecurrenciaModulo]:
    return (
        db.query(ReglaRecurrenciaModulo)
        .join(SerieModulo, SerieModulo.id == ReglaRecurrenciaModulo.serie_id)
        .options(
            joinedload(ReglaRecurrenciaModulo.serie).joinedload(SerieModulo.sala),
            joinedload(ReglaRecurrenciaModulo.serie).joinedload(SerieModulo.profesional),
        )
        .filter(
            SerieModulo.consultorio_id == consultorio_id,
            ReglaRecurrenciaModulo.estado == "activa",
            or_(
                and_(
                    SerieModulo.profesional_id.is_not(None),
                    _profesional_activo_en_consultorio(SerieModulo.consultorio_id, SerieModulo.profesional_id),
                ),
                and_(
                    SerieModulo.invitacion_id.is_not(None),
                    _invitacion_vigente(SerieModulo.consultorio_id, SerieModulo.invitacion_id, ahora),
                ),
            ),
        )
        .order_by(ReglaRecurrenciaModulo.dia_semana, ReglaRecurrenciaModulo.hora_inicio, ReglaRecurrenciaModulo.id)
        .all()
    )


def _profesional_activo_en_consultorio(consultorio_id, profesional_id):
    return exists(
        select(ConsultorioProfesional.id)
        .join(Profesional, Profesional.id == ConsultorioProfesional.profesional_id)
        .where(
            ConsultorioProfesional.consultorio_id == consultorio_id,
            ConsultorioProfesional.profesional_id == profesional_id,
            ConsultorioProfesional.estado.in_(("preparatorio", "activo")),
            Profesional.activo.is_(True),
        )
    )


def _invitacion_vigente(consultorio_id, invitacion_id, ahora: datetime):
    return exists(
        select(InvitacionConsultorio.id).where(
            InvitacionConsultorio.id == invitacion_id,
            InvitacionConsultorio.consultorio_id == consultorio_id,
            InvitacionConsultorio.estado.in_(("preparacion", "pendiente")),
            InvitacionConsultorio.vence_en > ahora,
        )
    )


def cancelar_reservas_sin_vigencia(db: Session, consultorio_id: int, ahora: datetime) -> None:
    """Release stale room reservations while retaining invitation and occurrence history."""
    db.execute(
        update(InvitacionConsultorio)
        .where(
            InvitacionConsultorio.consultorio_id == consultorio_id,
            InvitacionConsultorio.estado.in_(("preparacion", "pendiente")),
            InvitacionConsultorio.vence_en <= ahora,
        )
        .values(estado="expirada", token_hash=None)
    )
    invitaciones_invalidas = select(InvitacionConsultorio.id).where(
        InvitacionConsultorio.consultorio_id == consultorio_id,
        or_(
            InvitacionConsultorio.estado.not_in(("preparacion", "pendiente")),
            InvitacionConsultorio.vence_en.is_(None),
            InvitacionConsultorio.vence_en <= ahora,
        ),
    )
    db.execute(
        update(OcurrenciaModulo)
        .where(
            OcurrenciaModulo.consultorio_id == consultorio_id,
            OcurrenciaModulo.invitacion_id.in_(invitaciones_invalidas),
            OcurrenciaModulo.estado == "activa",
        )
        .values(estado="cancelada")
    )
    series_invalidas = select(SerieModulo.id).where(
        SerieModulo.consultorio_id == consultorio_id,
        SerieModulo.invitacion_id.in_(invitaciones_invalidas),
    )
    db.execute(
        update(ReglaRecurrenciaModulo)
        .where(ReglaRecurrenciaModulo.serie_id.in_(series_invalidas), ReglaRecurrenciaModulo.estado == "activa")
        .values(estado="cancelada")
    )
    series_sin_profesional_vigente = select(SerieModulo.id).where(
        SerieModulo.consultorio_id == consultorio_id,
        SerieModulo.profesional_id.is_not(None),
        ~_profesional_activo_en_consultorio(SerieModulo.consultorio_id, SerieModulo.profesional_id),
    )
    db.execute(
        update(OcurrenciaModulo)
        .where(
            OcurrenciaModulo.consultorio_id == consultorio_id,
            OcurrenciaModulo.profesional_id.is_not(None),
            ~_profesional_activo_en_consultorio(OcurrenciaModulo.consultorio_id, OcurrenciaModulo.profesional_id),
            OcurrenciaModulo.estado == "activa",
        )
        .values(estado="cancelada")
    )
    db.execute(
        update(ReglaRecurrenciaModulo)
        .where(ReglaRecurrenciaModulo.serie_id.in_(series_sin_profesional_vigente), ReglaRecurrenciaModulo.estado == "activa")
        .values(estado="cancelada")
    )


def listar_reglas_sala(db: Session, sala_id: int, ahora: datetime) -> list[ReglaRecurrenciaModulo]:
    return (
        db.query(ReglaRecurrenciaModulo)
        .join(SerieModulo, SerieModulo.id == ReglaRecurrenciaModulo.serie_id)
        .filter(
            SerieModulo.sala_id == sala_id,
            ReglaRecurrenciaModulo.estado == "activa",
            or_(
                and_(
                    SerieModulo.profesional_id.is_not(None),
                    _profesional_activo_en_consultorio(SerieModulo.consultorio_id, SerieModulo.profesional_id),
                ),
                and_(
                    SerieModulo.invitacion_id.is_not(None),
                    _invitacion_vigente(SerieModulo.consultorio_id, SerieModulo.invitacion_id, ahora),
                ),
            ),
        )
        .order_by(ReglaRecurrenciaModulo.id)
        .all()
    )


def listar_reglas_materializables(db: Session, consultorio_id: int, ahora: datetime, hoy: date, hasta: date):
    return (
        db.query(ReglaRecurrenciaModulo)
        .join(ReglaRecurrenciaModulo.serie)
        .filter(
            SerieModulo.consultorio_id == consultorio_id,
            ReglaRecurrenciaModulo.estado == "activa",
            ReglaRecurrenciaModulo.vigente_desde <= hasta,
            ReglaRecurrenciaModulo.vigente_hasta.is_(None)
            | (ReglaRecurrenciaModulo.vigente_hasta >= hoy),
            or_(
                and_(
                    SerieModulo.profesional_id.is_not(None),
                    _profesional_activo_en_consultorio(SerieModulo.consultorio_id, SerieModulo.profesional_id),
                ),
                and_(
                    SerieModulo.invitacion_id.is_not(None),
                    _invitacion_vigente(SerieModulo.consultorio_id, SerieModulo.invitacion_id, ahora),
                ),
            ),
        )
        .all()
    )


def bloquear_regla(db: Session, regla_id: int) -> ReglaRecurrenciaModulo | None:
    return (
        db.query(ReglaRecurrenciaModulo)
        .filter(ReglaRecurrenciaModulo.id == regla_id)
        .with_for_update()
        .populate_existing()
        .one_or_none()
    )


def obtener_ocurrencia(db: Session, consultorio_id: int, ocurrencia_id: int, bloquear: bool = False) -> OcurrenciaModulo | None:
    consulta = (
        db.query(OcurrenciaModulo)
        .options(joinedload(OcurrenciaModulo.sala), joinedload(OcurrenciaModulo.profesional))
        .filter(OcurrenciaModulo.consultorio_id == consultorio_id, OcurrenciaModulo.id == ocurrencia_id)
    )
    if bloquear:
        # Lock only the occurrence row; PostgreSQL rejects FOR UPDATE on the
        # nullable side of the joined professional relationship.
        consulta = consulta.with_for_update(of=OcurrenciaModulo)
    return consulta.one_or_none()


def listar_ocurrencias(db: Session, consultorio_id: int, desde: datetime, hasta: datetime, ahora: datetime) -> list[OcurrenciaModulo]:
    return (
        db.query(OcurrenciaModulo)
        .options(joinedload(OcurrenciaModulo.sala), joinedload(OcurrenciaModulo.profesional))
        .filter(
            OcurrenciaModulo.consultorio_id == consultorio_id,
            OcurrenciaModulo.fecha_inicio < hasta,
            OcurrenciaModulo.fecha_fin > desde,
            or_(
                and_(
                    OcurrenciaModulo.profesional_id.is_not(None),
                    _profesional_activo_en_consultorio(OcurrenciaModulo.consultorio_id, OcurrenciaModulo.profesional_id),
                ),
                and_(
                    OcurrenciaModulo.invitacion_id.is_not(None),
                    OcurrenciaModulo.estado == "activa",
                    _invitacion_vigente(OcurrenciaModulo.consultorio_id, OcurrenciaModulo.invitacion_id, ahora),
                ),
            ),
        )
        .order_by(OcurrenciaModulo.fecha_inicio, OcurrenciaModulo.sala_id)
        .all()
    )


def listar_mis_ocurrencias_activas(db: Session, usuario_id: int, ahora: datetime) -> list[OcurrenciaModulo]:
    """List only current/future modules authorized for this professional account."""
    return (
        db.query(OcurrenciaModulo)
        .options(joinedload(OcurrenciaModulo.sala))
        .join(Profesional, Profesional.id == OcurrenciaModulo.profesional_id)
        .join(
            ConsultorioProfesional,
            (ConsultorioProfesional.profesional_id == Profesional.id)
            & (ConsultorioProfesional.consultorio_id == OcurrenciaModulo.consultorio_id),
        )
        .join(Consultorio, Consultorio.id == OcurrenciaModulo.consultorio_id)
        .join(Sala, Sala.id == OcurrenciaModulo.sala_id)
        .filter(
            Profesional.usuario_id == usuario_id,
            Profesional.activo.is_(True),
            ConsultorioProfesional.estado.in_(("preparatorio", "activo")),
            Consultorio.estado == "activo",
            Sala.estado == "activa",
            OcurrenciaModulo.estado == "activa",
            OcurrenciaModulo.fecha_fin > ahora,
        )
        .order_by(OcurrenciaModulo.fecha_inicio, OcurrenciaModulo.sala_id)
        .all()
    )


def contar_turnos_afectados(db: Session, ocurrencia: OcurrenciaModulo) -> int:
    return (
        db.query(func.count(Turno.id))
        .filter(
            Turno.profesional_id == ocurrencia.profesional_id,
            Turno.estado.in_(ESTADOS_TURNO_ACTIVOS),
            Turno.fecha_hora < ocurrencia.fecha_fin,
            Turno.fecha_fin > ocurrencia.fecha_inicio,
        )
        .scalar()
        or 0
    )


def obtener_turnos_ocurrencia(db: Session, ocurrencia: OcurrenciaModulo) -> list[tuple[int, int, datetime, datetime]]:
    filas = (
        db.query(Turno.id, Turno.profesional_id, Turno.fecha_hora, Turno.fecha_fin)
        .filter(
            Turno.profesional_id == ocurrencia.profesional_id,
            Turno.estado.in_(ESTADOS_TURNO_ACTIVOS),
            Turno.fecha_hora < ocurrencia.fecha_fin,
            Turno.fecha_fin > ocurrencia.fecha_inicio,
        )
        .all()
    )
    return [(int(row[0]), int(row[1]), row[2], row[3]) for row in filas]


def buscar_ocurrencia_vigente_para_turno(
    db: Session, profesional_id: int, inicio: datetime, fin: datetime, bloquear: bool = True
) -> OcurrenciaModulo | None:
    consulta = (
        db.query(OcurrenciaModulo)
        .filter(
            OcurrenciaModulo.profesional_id == profesional_id,
            OcurrenciaModulo.estado == "activa",
            OcurrenciaModulo.fecha_inicio <= inicio,
            OcurrenciaModulo.fecha_fin >= fin,
            Consultorio.estado == "activo",
            Sala.estado == "activa",
        )
        .join(Consultorio, Consultorio.id == OcurrenciaModulo.consultorio_id)
        .join(Sala, Sala.id == OcurrenciaModulo.sala_id)
        .join(
            ConsultorioProfesional,
            (ConsultorioProfesional.profesional_id == profesional_id)
            & (ConsultorioProfesional.consultorio_id == OcurrenciaModulo.consultorio_id),
        )
        .join(Profesional, Profesional.id == profesional_id)
        .filter(Profesional.activo.is_(True), ConsultorioProfesional.estado == "activo")
        .order_by(OcurrenciaModulo.id)
    )
    if bloquear:
        consulta = consulta.with_for_update(of=OcurrenciaModulo)
    return consulta.first()


def materializar_existente(db: Session, regla_id: int, fecha_origen: date) -> OcurrenciaModulo | None:
    return (
        db.query(OcurrenciaModulo)
        .filter(OcurrenciaModulo.regla_id == regla_id, OcurrenciaModulo.fecha_origen == fecha_origen)
        .one_or_none()
    )


def crear_serie(db: Session, consultorio_id: int, sala_id: int, profesional_id: int, usuario_id: int) -> SerieModulo:
    item = SerieModulo(consultorio_id=consultorio_id, sala_id=sala_id, profesional_id=profesional_id, creado_por_usuario_id=usuario_id)
    db.add(item)
    db.flush()
    return item


def crear_regla(db: Session, serie_id: int, **datos) -> ReglaRecurrenciaModulo:
    item = ReglaRecurrenciaModulo(serie_id=serie_id, **datos)
    db.add(item)
    db.flush()
    return item


def crear_ocurrencia(db: Session, **datos) -> OcurrenciaModulo:
    item = OcurrenciaModulo(**datos)
    db.add(item)
    return item
