from sqlalchemy.orm import Session

from app.models.especialidad import Especialidad
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.profesional_especialidad import (
    profesionales_especialidades,
)
from app.schemas.prestacion import (
    PrestacionActualizar,
    PrestacionCrear,
)


def buscar_profesional_por_id(
    db: Session,
    profesional_id: int,
) -> Profesional | None:
    return (
        db.query(Profesional)
        .filter(Profesional.id == profesional_id)
        .first()
    )


def buscar_especialidad_por_id(
    db: Session,
    especialidad_id: int,
) -> Especialidad | None:
    return (
        db.query(Especialidad)
        .filter(Especialidad.id == especialidad_id)
        .first()
    )


def buscar_relacion_profesional_especialidad(
    db: Session,
    profesional_id: int,
    especialidad_id: int,
):
    return (
        db.query(profesionales_especialidades)
        .filter(
            profesionales_especialidades.c.profesional_id
            == profesional_id,
            profesionales_especialidades.c.especialidad_id
            == especialidad_id,
        )
        .first()
    )


def guardar_prestacion(
    db: Session,
    datos: PrestacionCrear,
) -> Prestacion:
    prestacion = Prestacion(
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        duracion_minutos=datos.duracion_minutos,
        precio=datos.precio,
        modalidad=datos.modalidad,
        profesional_id=datos.profesional_id,
        especialidad_id=datos.especialidad_id,
    )

    db.add(prestacion)

    return prestacion


def listar_prestaciones(
    db: Session,
) -> list[Prestacion]:
    return db.query(Prestacion).all()


def buscar_prestacion_por_id(
    db: Session,
    prestacion_id: int,
) -> Prestacion | None:
    return (
        db.query(Prestacion)
        .filter(Prestacion.id == prestacion_id)
        .first()
    )
    
def actualizar_prestacion(
    prestacion: Prestacion,
    datos: PrestacionActualizar,
) -> Prestacion:
    cambios = datos.model_dump(exclude_unset=True)

    for campo, valor in cambios.items():
        setattr(prestacion, campo, valor)

    return prestacion