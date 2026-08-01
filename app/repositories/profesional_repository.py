from sqlalchemy.orm import Session

from app.models.especialidad import Especialidad
from app.models.profesional import Profesional
from app.schemas.profesional import ProfesionalCrear


def buscar_especialidades_por_ids(
    db: Session,
    especialidad_ids: list[int],
) -> list[Especialidad]:
    return (
        db.query(Especialidad)
        .filter(Especialidad.id.in_(especialidad_ids))
        .all()
    )


def guardar_profesional(
    db: Session,
    datos: ProfesionalCrear,
    especialidades: list[Especialidad],
) -> Profesional:
    profesional = Profesional(
        nombre=datos.nombre,
        apellido=datos.apellido,
        matricula=datos.matricula,
        telefono=datos.telefono,
        email=datos.email,
        especialidades=especialidades,
    )

    db.add(profesional)

    return profesional


def buscar_todos(
    db: Session,
) -> list[Profesional]:
    return db.query(Profesional).all()


def buscar_por_id(
    db: Session,
    profesional_id: int,
) -> Profesional | None:
    return (
        db.query(Profesional)
        .filter(Profesional.id == profesional_id)
        .first()
    )