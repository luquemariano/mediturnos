from sqlalchemy.orm import Session

from app.models.disponibilidad import Disponibilidad
from app.models.profesional import Profesional
from app.schemas.disponibilidad import DisponibilidadCrear
from datetime import date, timedelta, time

from app.core.datetime_utils import fecha_hora_civil_a_utc

from app.models.prestacion import Prestacion
from app.models.turno import Turno


def buscar_profesional(
    db: Session,
    profesional_id: int,
) -> Profesional | None:
    return (
        db.query(Profesional)
        .filter(Profesional.id == profesional_id)
        .first()
    )


def guardar_disponibilidad(
    db: Session,
    datos: DisponibilidadCrear,
) -> Disponibilidad:
    disponibilidad = Disponibilidad(
        profesional_id=datos.profesional_id,
        dia_semana=datos.dia_semana,
        hora_inicio=datos.hora_inicio,
        hora_fin=datos.hora_fin,
    )

    db.add(disponibilidad)
    return disponibilidad


def buscar_todas(
    db: Session,
) -> list[Disponibilidad]:
    return db.query(Disponibilidad).all()


def buscar_por_profesional(
    db: Session,
    profesional_id: int,
) -> list[Disponibilidad]:
    return (
        db.query(Disponibilidad)
        .filter(
            Disponibilidad.profesional_id == profesional_id,
            Disponibilidad.activa.is_(True),
        )
        .order_by(
            Disponibilidad.dia_semana,
            Disponibilidad.hora_inicio,
        )
        .all()
    )


def buscar_por_dia(
    db: Session,
    profesional_id: int,
    dia_semana: int,
) -> list[Disponibilidad]:
    return (
        db.query(Disponibilidad)
        .filter(
            Disponibilidad.profesional_id == profesional_id,
            Disponibilidad.dia_semana == dia_semana,
            Disponibilidad.activa.is_(True),
        )
        .order_by(Disponibilidad.hora_inicio)
        .all()
    )
    
def buscar_prestacion(
    db: Session,
    prestacion_id: int,
) -> Prestacion | None:
    return (
        db.query(Prestacion)
        .filter(Prestacion.id == prestacion_id)
        .first()
    )


def buscar_turnos_del_dia(
    db: Session,
    profesional_id: int,
    fecha: date,
    turno_id_excluido: int | None = None,
) -> list[Turno]:
    inicio_dia = fecha_hora_civil_a_utc(
        fecha,
        time.min,
    )

    fin_dia = fecha_hora_civil_a_utc(
        fecha + timedelta(days=1),
        time.min,
    )

    consulta = (
        db.query(Turno)
        .join(
            Prestacion,
            Turno.prestacion_id == Prestacion.id,
        )
        .filter(
            Prestacion.profesional_id == profesional_id,
            Turno.fecha_hora >= inicio_dia,
            Turno.fecha_hora < fin_dia,
            Turno.estado != "cancelado",
        )
    )

    if turno_id_excluido is not None:
        consulta = consulta.filter(
            Turno.id != turno_id_excluido,
        )

    return consulta.all()
