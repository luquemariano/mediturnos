from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.profesional import Profesional
from app.repositories.profesional_repository import (
    buscar_especialidades_por_ids,
    buscar_profesional_por_usuario_id,
    buscar_por_id,
    buscar_todos,
    guardar_profesional,
)
from app.schemas.profesional import ProfesionalCrear


class EspecialidadesInvalidasError(Exception):
    pass


class EspecialidadesDuplicadasError(Exception):
    pass


def crear_profesional(
    db: Session,
    datos: ProfesionalCrear,
) -> Profesional:
    especialidad_ids = [
        item.especialidad_id
        for item in datos.especialidades
    ]

    if len(especialidad_ids) != len(set(especialidad_ids)):
        raise EspecialidadesDuplicadasError

    especialidades = buscar_especialidades_por_ids(
        db,
        especialidad_ids,
    )

    ids_encontrados = {
        especialidad.id
        for especialidad in especialidades
    }

    ids_solicitados = set(especialidad_ids)

    if ids_encontrados != ids_solicitados:
        raise EspecialidadesInvalidasError

    profesional = guardar_profesional(
        db,
        datos,
        especialidades,
    )

    try:
        db.commit()
        db.refresh(profesional)

    except IntegrityError:
        db.rollback()
        raise

    return profesional


def obtener_profesionales(
    db: Session,
) -> list[Profesional]:
    return buscar_todos(db)


def obtener_profesional_por_id(
    db: Session,
    profesional_id: int,
) -> Profesional | None:
    return buscar_por_id(
        db,
        profesional_id,
    )


def obtener_mi_profesional(
    db: Session,
    usuario_id: int,
) -> Profesional:
    profesional = buscar_profesional_por_usuario_id(
        db,
        usuario_id,
    )

    if profesional is None:
        raise HTTPException(
            status_code=404,
            detail="El usuario no tiene un profesional asociado.",
        )

    return profesional