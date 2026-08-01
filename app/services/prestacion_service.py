from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.prestacion_repository import (
    actualizar_prestacion,
    buscar_especialidad_por_id,
    buscar_prestacion_por_id,
    buscar_profesional_por_id,
    buscar_relacion_profesional_especialidad,
    guardar_prestacion,
    listar_prestaciones,
)
from app.schemas.prestacion import PrestacionCrear
from app.models.prestacion import Prestacion


def crear_prestacion(
    db: Session,
    datos: PrestacionCrear,
):
    profesional = buscar_profesional_por_id(
        db,
        datos.profesional_id,
    )

    if profesional is None:
        raise HTTPException(
            status_code=404,
            detail="Profesional no encontrado.",
        )

    especialidad = buscar_especialidad_por_id(
        db,
        datos.especialidad_id,
    )

    if especialidad is None:
        raise HTTPException(
            status_code=404,
            detail="Especialidad no encontrada.",
        )

    relacion = buscar_relacion_profesional_especialidad(
        db,
        datos.profesional_id,
        datos.especialidad_id,
    )

    if relacion is None:
        raise HTTPException(
            status_code=400,
            detail="La especialidad no pertenece al profesional.",
        )

    prestacion = guardar_prestacion(
        db,
        datos,
    )

    db.commit()
    db.refresh(prestacion)

    return prestacion


def obtener_prestaciones(
    db: Session,
):
    return listar_prestaciones(db)


def obtener_prestacion(
    db: Session,
    prestacion_id: int,
):
    prestacion = buscar_prestacion_por_id(
        db,
        prestacion_id,
    )

    if prestacion is None:
        raise HTTPException(
            status_code=404,
            detail="Prestación no encontrada.",
        )

    return prestacion

def modificar_prestacion(
    db: Session,
    prestacion_id: int,
    datos: PrestacionActualizar,
) -> Prestacion:
    prestacion = buscar_prestacion_por_id(
        db,
        prestacion_id,
    )

    if prestacion is None:
        raise HTTPException(
            status_code=404,
            detail="Prestación no encontrada.",
        )

    prestacion_actualizada = actualizar_prestacion(
        prestacion,
        datos,
    )

    db.commit()
    db.refresh(prestacion_actualizada)

    return prestacion_actualizada


def desactivar_prestacion(
    db: Session,
    prestacion_id: int,
) -> Prestacion:
    prestacion = buscar_prestacion_por_id(
        db,
        prestacion_id,
    )

    if prestacion is None:
        raise HTTPException(
            status_code=404,
            detail="Prestación no encontrada.",
        )

    prestacion.activa = False

    db.commit()
    db.refresh(prestacion)

    return prestacion