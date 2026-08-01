from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.turno import Turno
from app.repositories.turno_repository import (
    buscar_conflicto_horario,
    buscar_paciente_por_id,
    buscar_por_id,
    buscar_prestacion_por_id,
    buscar_todos,
    guardar_turno,
)
from app.schemas.turno import (
    TurnoActualizarEstado,
    TurnoCrear,
    TurnoReprogramar,
)
from app.services.disponibilidad_service import obtener_horarios_libres

def crear_turno(
    db: Session,
    datos: TurnoCrear,
) -> Turno:
    paciente = buscar_paciente_por_id(
        db,
        datos.paciente_id,
    )

    if paciente is None:
        raise HTTPException(
            status_code=404,
            detail="Paciente no encontrado.",
        )

    prestacion = buscar_prestacion_por_id(
        db,
        datos.prestacion_id,
    )

    if prestacion is None:
        raise HTTPException(
            status_code=404,
            detail="Prestación no encontrada.",
        )

    if not paciente.activo:
        raise HTTPException(
            status_code=400,
            detail="El paciente está inactivo.",
        )

    if not prestacion.activa:
        raise HTTPException(
            status_code=400,
            detail="La prestación está inactiva.",
        )

    if datos.fecha_hora <= datetime.now():
        raise HTTPException(
            status_code=400,
            detail="La fecha y hora deben ser futuras.",
        )

    conflicto = buscar_conflicto_horario(
        db,
        prestacion.profesional_id,
        datos.fecha_hora,
    )

    if conflicto is not None:
        raise HTTPException(
            status_code=409,
            detail="El profesional ya tiene un turno en ese horario.",
        )

    turno = guardar_turno(db, datos)

    db.commit()
    db.refresh(turno)

    return turno


def obtener_turnos(
    db: Session,
) -> list[Turno]:
    return buscar_todos(db)


def obtener_turno(
    db: Session,
    turno_id: int,
) -> Turno:
    turno = buscar_por_id(db, turno_id)

    if turno is None:
        raise HTTPException(
            status_code=404,
            detail="Turno no encontrado.",
        )

    return turno


def cambiar_estado_turno(
    db: Session,
    turno_id: int,
    datos: TurnoActualizarEstado,
) -> Turno:
    turno = obtener_turno(db, turno_id)

    turno.estado = datos.estado

    db.commit()
    db.refresh(turno)

    return turno

def reprogramar_turno(
    db: Session,
    turno_id: int,
    datos: TurnoReprogramar,
) -> Turno:
    turno = obtener_turno(
        db,
        turno_id,
    )

    if turno.estado in {"cancelado", "finalizado"}:
        raise HTTPException(
            status_code=400,
            detail="No se puede reprogramar un turno cancelado o finalizado.",
        )

    if datos.fecha_hora <= datetime.now():
        raise HTTPException(
            status_code=400,
            detail="La nueva fecha y hora deben ser futuras.",
        )

    horarios_libres = obtener_horarios_libres(
        db,
        turno.prestacion_id,
        datos.fecha_hora.date(),
    )

    fechas_disponibles = {
        horario["fecha_hora"]
        for horario in horarios_libres
    }

    if datos.fecha_hora not in fechas_disponibles:
        raise HTTPException(
            status_code=409,
            detail="El horario seleccionado no está disponible.",
        )

    turno.fecha_hora = datos.fecha_hora

    db.commit()
    db.refresh(turno)

    return turno