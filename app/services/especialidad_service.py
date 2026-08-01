from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.especialidad import Especialidad
from app.repositories.especialidad_repository import (
    actualizar_especialidad,
    buscar_por_id,
    buscar_todas,
    guardar_especialidad,
)
from app.schemas.especialidad import (
    EspecialidadActualizar,
    EspecialidadCrear,
)


def crear_especialidad(
    db: Session,
    datos: EspecialidadCrear,
) -> Especialidad:
    especialidad = guardar_especialidad(db, datos)

    try:
        db.commit()
        db.refresh(especialidad)

    except IntegrityError:
        db.rollback()
        raise

    return especialidad


def obtener_especialidades(
    db: Session,
) -> list[Especialidad]:
    return buscar_todas(db)


def obtener_especialidad_por_id(
    db: Session,
    especialidad_id: int,
) -> Especialidad | None:
    return buscar_por_id(
        db,
        especialidad_id,
    )
    
def modificar_especialidad(
    db: Session,
    especialidad: Especialidad,
    datos: EspecialidadActualizar,
) -> Especialidad:
    especialidad_actualizada = actualizar_especialidad(
        especialidad,
        datos,
    )

    try:
        db.commit()
        db.refresh(especialidad_actualizada)

    except IntegrityError:
        db.rollback()
        raise

    return especialidad_actualizada