from datetime import datetime, timedelta

from sqlalchemy.orm import Session, joinedload

from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.turno import Turno
from app.schemas.turno import TurnoCrear
from app.core.datetime_utils import desde_base_utc



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

    consulta = (
        db.query(Turno)
        .join(
            Prestacion,
            Turno.prestacion_id == Prestacion.id,
        )
        .options(joinedload(Turno.prestacion))
        .filter(
            Prestacion.profesional_id == profesional_id,
            Turno.fecha_hora < fin_nuevo,
            Turno.estado != "cancelado",
        )
    )

    if turno_id_excluido is not None:
        consulta = consulta.filter(
            Turno.id != turno_id_excluido,
        )

    for turno in consulta.all():
        inicio_existente = desde_base_utc(
            turno.fecha_hora,
        )
        fin_existente = inicio_existente + timedelta(
            minutes=turno.prestacion.duracion_minutos,
        )

        if (
            inicio_nuevo < fin_existente
            and fin_nuevo > inicio_existente
        ):
            return turno

    return None


def guardar_turno(
    db: Session,
    datos: TurnoCrear,
) -> Turno:
    turno = Turno(
        paciente_id=datos.paciente_id,
        prestacion_id=datos.prestacion_id,
        fecha_hora=datos.fecha_hora,
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
        .join(
            Prestacion,
            Turno.prestacion_id == Prestacion.id,
        )
        .filter(
            Prestacion.profesional_id == profesional_id,
        )
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
        .join(
            Prestacion,
            Turno.prestacion_id == Prestacion.id,
        )
        .filter(
            Turno.id == turno_id,
            Prestacion.profesional_id == profesional_id,
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
