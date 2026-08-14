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
    listar_prestaciones_de_profesional,
    buscar_prestacion_de_profesional,
    buscar_nombre_de_profesional,
)
from app.schemas.prestacion import (
    PrestacionActualizar,
    PrestacionCrear,
    PrestacionProfesionalCrear,
    PrestacionProfesionalActualizar,
)
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

def obtener_prestaciones_profesional(db: Session, profesional_id: int) -> list[Prestacion]:
    return listar_prestaciones_de_profesional(db, profesional_id)

def crear_prestacion_profesional(db: Session, profesional_id: int, datos: PrestacionProfesionalCrear) -> Prestacion:
    if buscar_relacion_profesional_especialidad(db, profesional_id, datos.especialidad_id) is None:
        raise HTTPException(status_code=400, detail="La especialidad no pertenece al profesional.")
    if buscar_nombre_de_profesional(db, profesional_id, datos.nombre):
        raise HTTPException(status_code=409, detail="Ya existe una prestación con ese nombre.")
    prestacion = Prestacion(profesional_id=profesional_id, **datos.model_dump())
    db.add(prestacion); db.commit(); db.refresh(prestacion)
    return prestacion

def modificar_prestacion_profesional(db: Session, profesional_id: int, prestacion_id: int, datos: PrestacionProfesionalActualizar) -> Prestacion:
    prestacion = buscar_prestacion_de_profesional(db, prestacion_id, profesional_id)
    if prestacion is None:
        raise HTTPException(status_code=404, detail="Prestación no encontrada.")
    cambios = datos.model_dump(exclude_unset=True)
    if "nombre" in cambios and buscar_nombre_de_profesional(db, profesional_id, cambios["nombre"], prestacion_id):
        raise HTTPException(status_code=409, detail="Ya existe una prestación con ese nombre.")
    for campo, valor in cambios.items(): setattr(prestacion, campo, valor)
    db.commit(); db.refresh(prestacion)
    return prestacion

def desactivar_prestacion_profesional(db: Session, profesional_id: int, prestacion_id: int) -> Prestacion:
    prestacion = buscar_prestacion_de_profesional(db, prestacion_id, profesional_id)
    if prestacion is None:
        raise HTTPException(status_code=404, detail="Prestación no encontrada.")
    prestacion.activa = False
    db.commit(); db.refresh(prestacion)
    return prestacion
