from sqlalchemy.orm import Session

from app.models.especialidad import Especialidad
from app.schemas.especialidad import EspecialidadCrear
from app.schemas.especialidad import (
    EspecialidadActualizar,
    EspecialidadCrear,
)


def guardar_especialidad(
    db: Session,
    datos: EspecialidadCrear,
) -> Especialidad:
    especialidad = Especialidad(
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        duracion_turno_minutos=datos.duracion_turno_minutos,
    )

    db.add(especialidad)

    return especialidad


def buscar_todas(
    db: Session,
) -> list[Especialidad]:
    return db.query(Especialidad).all()


def buscar_por_id(
    db: Session,
    especialidad_id: int,
) -> Especialidad | None:
    return (
        db.query(Especialidad)
        .filter(Especialidad.id == especialidad_id)
        .first()
    )

def actualizar_especialidad(
    especialidad: Especialidad,
    datos: EspecialidadActualizar,
) -> Especialidad:
    cambios = datos.model_dump(exclude_unset=True)

    for campo, valor in cambios.items():
        setattr(especialidad, campo, valor)

    return especialidad