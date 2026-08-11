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
    buscar_turno_de_profesional,
    buscar_turnos_por_paciente_id,
    buscar_turnos_por_profesional_id,
    guardar_turno,
    buscar_turno_de_paciente,
)
from app.schemas.turno import (
    TurnoActualizarEstado,
    TurnoCrear,
    TurnoCrearPropio,
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
        prestacion.duracion_minutos,
    )

    if conflicto is not None:
        raise HTTPException(
            status_code=409,
            detail="El profesional ya tiene un turno en ese horario.",
        )

    turno = guardar_turno(
        db,
        datos,
    )

    db.commit()
    db.refresh(turno)

    return turno


def crear_turno_propio(
    db: Session,
    paciente_id: int,
    datos: TurnoCrearPropio,
) -> Turno:
    datos_turno = TurnoCrear(
        paciente_id=paciente_id,
        prestacion_id=datos.prestacion_id,
        fecha_hora=datos.fecha_hora,
        observaciones=datos.observaciones,
    )

    return crear_turno(
        db,
        datos_turno,
    )


def obtener_turnos(
    db: Session,
) -> list[Turno]:
    return buscar_todos(db)


def obtener_turno(
    db: Session,
    turno_id: int,
) -> Turno:
    turno = buscar_por_id(
        db,
        turno_id,
    )

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
    turno = obtener_turno(
        db,
        turno_id,
    )

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
            detail=(
                "No se puede reprogramar un turno "
                "cancelado o finalizado."
            ),
        )

    if datos.fecha_hora <= datetime.now():
        raise HTTPException(
            status_code=400,
            detail="La nueva fecha y hora deben ser futuras.",
        )

    conflicto = buscar_conflicto_horario(
        db,
        turno.prestacion.profesional_id,
        datos.fecha_hora,
        turno.prestacion.duracion_minutos,
        turno_id_excluido=turno.id,
    )

    if conflicto is not None:
        raise HTTPException(
            status_code=409,
            detail="El profesional ya tiene un turno en ese horario.",
        )

    horarios_libres = obtener_horarios_libres(
        db,
        turno.prestacion_id,
        datos.fecha_hora.date(),
        turno_id_excluido=turno.id,
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


def obtener_turnos_de_paciente(
    db: Session,
    paciente_id: int,
) -> list[Turno]:
    return buscar_turnos_por_paciente_id(
        db,
        paciente_id,
    )


def obtener_agenda_de_profesional(
    db: Session,
    profesional_id: int,
    estado: str | None = None,
) -> list[Turno]:
    estados_validos = {
        "reservado",
        "confirmado",
        "cancelado",
        "ausente",
        "finalizado",
    }

    if (
        estado is not None
        and estado not in estados_validos
    ):
        raise HTTPException(
            status_code=400,
            detail="Estado de turno inválido.",
        )

    return buscar_turnos_por_profesional_id(
        db,
        profesional_id,
        estado,
    )


def finalizar_turno_profesional(
    db: Session,
    turno_id: int,
    profesional_id: int,
) -> Turno:
    turno = buscar_turno_de_profesional(
        db,
        turno_id,
        profesional_id,
    )

    if turno is None:
        raise HTTPException(
            status_code=404,
            detail="Turno no encontrado.",
        )

    if turno.estado == "cancelado":
        raise HTTPException(
            status_code=400,
            detail="No se puede finalizar un turno cancelado.",
        )

    if turno.estado == "finalizado":
        raise HTTPException(
            status_code=409,
            detail="El turno ya se encuentra finalizado.",
        )

    turno.estado = "finalizado"

    db.commit()
    db.refresh(turno)

    return turno


def marcar_ausente_turno_profesional(
    db: Session,
    turno_id: int,
    profesional_id: int,
) -> Turno:
    turno = buscar_turno_de_profesional(
        db,
        turno_id,
        profesional_id,
    )

    if turno is None:
        raise HTTPException(
            status_code=404,
            detail="Turno no encontrado.",
        )

    if turno.estado == "cancelado":
        raise HTTPException(
            status_code=400,
            detail="No se puede marcar ausente un turno cancelado.",
        )

    if turno.estado == "finalizado":
        raise HTTPException(
            status_code=400,
            detail="No se puede marcar ausente un turno finalizado.",
        )

    if turno.estado == "ausente":
        raise HTTPException(
            status_code=409,
            detail="El turno ya está marcado como ausente.",
        )

    turno.estado = "ausente"

    db.commit()
    db.refresh(turno)

    return turno

def cancelar_turno_paciente(
    db: Session,
    turno_id: int,
    paciente_id: int,
) -> Turno:
    turno = buscar_turno_de_paciente(
        db,
        turno_id,
        paciente_id,
    )

    if turno is None:
        raise HTTPException(
            status_code=404,
            detail="Turno no encontrado.",
        )

    if turno.estado == "cancelado":
        raise HTTPException(
            status_code=409,
            detail="El turno ya se encuentra cancelado.",
        )

    if turno.estado == "finalizado":
        raise HTTPException(
            status_code=400,
            detail="No se puede cancelar un turno finalizado.",
        )

    if turno.estado == "ausente":
        raise HTTPException(
            status_code=400,
            detail="No se puede cancelar un turno marcado como ausente.",
        )

    turno.estado = "cancelado"

    db.commit()
    db.refresh(turno)

    return turno
