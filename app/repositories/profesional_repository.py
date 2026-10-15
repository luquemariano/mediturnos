from sqlalchemy.orm import Session, selectinload

from app.models.especialidad import Especialidad
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.profesional_especialidad import ProfesionalEspecialidad
from app.schemas.profesional import (
    EspecialidadProfesionalCrear,
    ProfesionalActualizar,
    ProfesionalCrear,
)

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
    actividad_profesional,
) -> Profesional:

    profesional = Profesional(
        nombre=datos.nombre,
        apellido=datos.apellido,
        matricula=datos.matricula,
        actividad_profesional=actividad_profesional,
        telefono=datos.telefono,
        email=datos.email,
    )

    db.add(profesional)

    mapa = {
        e.id: e
        for e in especialidades
    }

    duraciones_por_especialidad = {
        item.especialidad_id: item.duracion_turno_minutos
        for item in (datos.especialidades or [])
    }

    for especialidad in especialidades:

        relacion = ProfesionalEspecialidad(
            especialidad=mapa[especialidad.id],
            duracion_turno_minutos=duraciones_por_especialidad.get(
                especialidad.id, especialidad.duracion_turno_minutos,
            ),
        )

        profesional.especialidades_asignadas.append(relacion)

    return profesional


def buscar_todos(
    db: Session,
):
    return (
        db.query(Profesional)
        .options(
            selectinload(
                Profesional.especialidades_asignadas
            )
        )
        .all()
    )


def buscar_especialidades_con_prestaciones(
    db: Session,
    profesional_id: int,
    especialidad_ids: set[int],
) -> list[Especialidad]:
    if not especialidad_ids:
        return []

    return (
        db.query(Especialidad)
        .join(
            Prestacion,
            Prestacion.especialidad_id
            == Especialidad.id,
        )
        .filter(
            Prestacion.profesional_id
            == profesional_id,
            Especialidad.id.in_(especialidad_ids),
        )
        .distinct()
        .all()
    )


def buscar_por_id(
    db: Session,
    profesional_id: int,
):
    return (
        db.query(Profesional)
        .options(
            selectinload(
                Profesional.especialidades_asignadas
            )
        )
        .filter(Profesional.id == profesional_id)
        .first()
    )


def actualizar_profesional(
    profesional: Profesional,
    datos: ProfesionalActualizar,
) -> Profesional:
    cambios = datos.model_dump(
        exclude_unset=True,
        exclude={"especialidades"},
    )

    for campo, valor in cambios.items():
        setattr(profesional, campo, valor)

    return profesional


def reemplazar_especialidades_profesional(
    profesional: Profesional,
    asignaciones: list[EspecialidadProfesionalCrear],
    especialidades: list[Especialidad],
) -> Profesional:
    relaciones_existentes = {
        relacion.especialidad_id: relacion
        for relacion
        in profesional.especialidades_asignadas
    }
    especialidades_por_id = {
        especialidad.id: especialidad
        for especialidad in especialidades
    }
    relaciones_actualizadas = []

    for asignacion in asignaciones:
        relacion = relaciones_existentes.get(
            asignacion.especialidad_id
        )

        if relacion is None:
            relacion = ProfesionalEspecialidad(
                especialidad=(
                    especialidades_por_id[
                        asignacion.especialidad_id
                    ]
                ),
            )

        relacion.duracion_turno_minutos = (
            asignacion.duracion_turno_minutos
        )
        relaciones_actualizadas.append(relacion)

    profesional.especialidades_asignadas = (
        relaciones_actualizadas
    )

    return profesional


def buscar_profesional_por_usuario_id(
    db: Session,
    usuario_id: int,
) -> Profesional | None:
    return (
        db.query(Profesional)
        .filter(Profesional.usuario_id == usuario_id)
        .first()
    )
