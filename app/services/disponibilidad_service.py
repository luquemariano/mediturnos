from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.disponibilidad import Disponibilidad
from app.repositories.disponibilidad_repository import (
    buscar_por_dia,
    buscar_por_profesional,
    buscar_prestacion,
    buscar_profesional,
    buscar_todas,
    buscar_turnos_del_dia,
    guardar_disponibilidad,
)
from app.schemas.disponibilidad import DisponibilidadCrear
from datetime import date, datetime, timedelta


def crear_disponibilidad(
    db: Session,
    datos: DisponibilidadCrear,
) -> Disponibilidad:
    profesional = buscar_profesional(
        db,
        datos.profesional_id,
    )

    if profesional is None:
        raise HTTPException(
            status_code=404,
            detail="Profesional no encontrado.",
        )

    if not profesional.activo:
        raise HTTPException(
            status_code=400,
            detail="El profesional está inactivo.",
        )

    disponibilidad = guardar_disponibilidad(
        db,
        datos,
    )

    db.commit()
    db.refresh(disponibilidad)

    return disponibilidad


def obtener_disponibilidades(
    db: Session,
) -> list[Disponibilidad]:
    return buscar_todas(db)


def obtener_disponibilidades_profesional(
    db: Session,
    profesional_id: int,
) -> list[Disponibilidad]:
    profesional = buscar_profesional(
        db,
        profesional_id,
    )

    if profesional is None:
        raise HTTPException(
            status_code=404,
            detail="Profesional no encontrado.",
        )

    return buscar_por_profesional(
        db,
        profesional_id,
    )


def validar_turno_dentro_disponibilidad(
    db: Session,
    profesional_id: int,
    fecha_hora: datetime,
    duracion_minutos: int,
) -> None:
    disponibilidades = buscar_por_dia(
        db,
        profesional_id,
        fecha_hora.weekday(),
    )
    fin_turno = fecha_hora + timedelta(
        minutes=duracion_minutos,
    )

    for disponibilidad in disponibilidades:
        inicio_disponibilidad = datetime.combine(
            fecha_hora.date(),
            disponibilidad.hora_inicio,
        )
        fin_disponibilidad = datetime.combine(
            fecha_hora.date(),
            disponibilidad.hora_fin,
        )

        if (
            inicio_disponibilidad <= fecha_hora
            and fin_turno <= fin_disponibilidad
        ):
            return

    raise HTTPException(
        status_code=409,
        detail=(
            "El horario seleccionado no está dentro de la "
            "disponibilidad del profesional."
        ),
    )


def obtener_horarios_libres(
    db: Session,
    prestacion_id: int,
    fecha: date,
    turno_id_excluido: int | None = None,
) -> list[dict]:
    prestacion = buscar_prestacion(
        db,
        prestacion_id,
    )

    if prestacion is None:
        raise HTTPException(
            status_code=404,
            detail="Prestación no encontrada.",
        )

    if not prestacion.activa:
        raise HTTPException(
            status_code=400,
            detail="La prestación está inactiva.",
        )

    if fecha < date.today():
        raise HTTPException(
            status_code=400,
            detail="La fecha no puede ser anterior a hoy.",
        )

    dia_semana = fecha.weekday()

    disponibilidades = buscar_por_dia(
        db,
        prestacion.profesional_id,
        dia_semana,
    )

    if not disponibilidades:
        return []

    turnos_ocupados = buscar_turnos_del_dia(
        db,
        prestacion.profesional_id,
        fecha,
        turno_id_excluido,
    )

    duracion = timedelta(
        minutes=prestacion.duracion_minutos,
    )

    horarios_libres = []

    for disponibilidad in disponibilidades:
        horario_actual = datetime.combine(
            fecha,
            disponibilidad.hora_inicio,
        )

        fin_disponibilidad = datetime.combine(
            fecha,
            disponibilidad.hora_fin,
        )

        while horario_actual + duracion <= fin_disponibilidad:
            fin_horario = horario_actual + duracion

            existe_conflicto = False

            for turno in turnos_ocupados:
                inicio_turno = turno.fecha_hora
                fin_turno = (
                    inicio_turno
                    + timedelta(
                        minutes=turno.prestacion.duracion_minutos,
                    )
                )

                if (
                    horario_actual < fin_turno
                    and fin_horario > inicio_turno
                ):
                    existe_conflicto = True
                    break

            if not existe_conflicto:
                horarios_libres.append(
                    {
                        "fecha_hora": horario_actual,
                    }
                )

            horario_actual += duracion

    return horarios_libres
