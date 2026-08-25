from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.turno import Turno
from app.schemas.turno import TurnoCrear


ESPACIO_LOCK_AGENDA = 73421


def bloquear_agenda_profesional(
    db: Session,
    profesional_id: int,
) -> None:
    bind = db.get_bind()

    if bind.dialect.name != "postgresql":
        return

    db.execute(
        select(
            func.pg_advisory_xact_lock(
                ESPACIO_LOCK_AGENDA,
                profesional_id,
            )
        )
    )
def buscar_paciente_por_id(
    db: Session,
    paciente_id: int,
) -> Paciente | None:
    return (
        db.query(Paciente)
        .filter(Paciente.id == paciente_id)
        .first()
    )


def buscar_prestacion_por_id(
    db: Session,
    prestacion_id: int,
) -> Prestacion | None:
    return (
        db.query(Prestacion)
        .filter(Prestacion.id == prestacion_id)
        .first()
    )


def buscar_conflicto_horario(
    db: Session,
    profesional_id: int,
    inicio_nuevo: datetime,
    duracion_minutos: int,
    turno_id_excluido: int | None = None,
) -> Turno | None:
    fin_nuevo = inicio_nuevo + timedelta(
        minutes=duracion_minutos,
    )

    consulta = db.query(Turno).filter(
        Turno.profesional_id == profesional_id,
        Turno.fecha_hora < fin_nuevo,
        Turno.fecha_fin > inicio_nuevo,
        Turno.estado != "cancelado",
    )

    if turno_id_excluido is not None:
        consulta = consulta.filter(
            Turno.id != turno_id_excluido,
        )

    return consulta.first()


def guardar_turno(
    db: Session,
    datos: TurnoCrear,
    profesional_id: int,
    fecha_fin: datetime,
) -> Turno:
    turno = Turno(
        paciente_id=datos.paciente_id,
        prestacion_id=datos.prestacion_id,
        profesional_id=profesional_id,
        fecha_hora=datos.fecha_hora,
        fecha_fin=fecha_fin,
        observaciones=datos.observaciones,
    )

    db.add(turno)

    return turno


def buscar_todos(
    db: Session,
) -> list[Turno]:
    return (
        db.query(Turno)
        .options(
            joinedload(Turno.paciente),
            joinedload(Turno.prestacion)
            .joinedload(Prestacion.profesional),
            joinedload(Turno.prestacion)
            .joinedload(Prestacion.especialidad),
        )
        .order_by(Turno.fecha_hora)
        .all()
    )


def buscar_por_id(
    db: Session,
    turno_id: int,
) -> Turno | None:
    return (
        db.query(Turno)
        .filter(Turno.id == turno_id)
        .first()
    )


def buscar_turnos_por_paciente_id(
    db: Session,
    paciente_id: int,
) -> list[Turno]:
    return (
        db.query(Turno)
        .filter(
            Turno.paciente_id == paciente_id,
        )
        .order_by(Turno.fecha_hora)
        .all()
    )


def buscar_turnos_por_profesional_id(
    db: Session,
    profesional_id: int,
    estado: str | None = None,
) -> list[Turno]:
    consulta = (
        db.query(Turno)
        .filter(Turno.profesional_id == profesional_id)
    )

    if estado is not None:
        consulta = consulta.filter(
            Turno.estado == estado,
        )

    return (
        consulta
        .order_by(Turno.fecha_hora)
        .all()
    )
    
def buscar_turno_de_profesional(
    db: Session,
    turno_id: int,
    profesional_id: int,
) -> Turno | None:
    return (
        db.query(Turno)
        .filter(
            Turno.id == turno_id,
            Turno.profesional_id == profesional_id,
        )
        .first()
    )
    
def buscar_turno_de_paciente(
    db: Session,
    turno_id: int,
    paciente_id: int,
) -> Turno | None:
    return (
        db.query(Turno)
        .filter(
            Turno.id == turno_id,
            Turno.paciente_id == paciente_id,
        )
        .first()
    )
