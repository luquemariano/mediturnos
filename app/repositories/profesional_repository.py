from sqlalchemy.orm import Session

from app.models.especialidad import Especialidad
from app.models.profesional import Profesional
from app.models.profesional_especialidad import ProfesionalEspecialidad
from app.schemas.profesional import ProfesionalCrear
from sqlalchemy.orm import Session

from app.models.profesional import Profesional

def buscar_especialidades_por_ids(
    db: Session,
    ids: list[int],
) -> list[Especialidad]:
    return (
        db.query(Especialidad)
        .filter(Especialidad.id.in_(ids))
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
    )

    db.add(profesional)

    mapa = {
        e.id: e
        for e in especialidades
    }

    for item in datos.especialidades:

        relacion = ProfesionalEspecialidad(
            especialidad=mapa[item.especialidad_id],
            duracion_turno_minutos=item.duracion_turno_minutos,
        )

        profesional.especialidades_asignadas.append(relacion)

    return profesional


def buscar_todos(
    db: Session,
):
    return db.query(Profesional).all()


def buscar_por_id(
    db: Session,
    profesional_id: int,
):
    return (
        db.query(Profesional)
        .filter(Profesional.id == profesional_id)
        .first()
    )
def buscar_profesional_por_usuario_id(
    db: Session,
    usuario_id: int,
) -> Profesional | None:
    return (
        db.query(Profesional)
        .filter(Profesional.usuario_id == usuario_id)
        .first()
    )