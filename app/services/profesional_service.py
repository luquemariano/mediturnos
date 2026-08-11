from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.profesional import Profesional
from app.models.especialidad import Especialidad
from app.repositories.profesional_repository import (
    actualizar_profesional,
    buscar_especialidades_por_ids,
    buscar_especialidades_con_prestaciones,
    buscar_profesional_por_usuario_id,
    buscar_por_id,
    buscar_todos,
    guardar_profesional,
    reemplazar_especialidades_profesional,
)
from app.schemas.profesional import (
    EspecialidadProfesionalCrear,
    ProfesionalActualizar,
    ProfesionalCrear,
)


class EspecialidadesInvalidasError(Exception):
    pass


class EspecialidadesDuplicadasError(Exception):
    pass


class EspecialidadesConPrestacionesError(Exception):
    def __init__(self, nombres: list[str]):
        self.nombres = nombres
        super().__init__(nombres)


def validar_especialidades(
    db: Session,
    asignaciones: list[EspecialidadProfesionalCrear],
) -> list[Especialidad]:
    especialidad_ids = [
        item.especialidad_id
        for item in asignaciones
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

    if ids_encontrados != set(especialidad_ids):
        raise EspecialidadesInvalidasError

    return especialidades


def crear_profesional(
    db: Session,
    datos: ProfesionalCrear,
) -> Profesional:
    especialidades = validar_especialidades(
        db,
        datos.especialidades,
    )

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


def modificar_profesional(
    db: Session,
    profesional: Profesional,
    datos: ProfesionalActualizar,
) -> Profesional:
    especialidades = None

    if datos.especialidades is not None:
        especialidades = validar_especialidades(
            db,
            datos.especialidades,
        )

        ids_actuales = {
            relacion.especialidad_id
            for relacion
            in profesional.especialidades_asignadas
        }
        ids_solicitados = {
            asignacion.especialidad_id
            for asignacion in datos.especialidades
        }
        ids_a_quitar = ids_actuales - ids_solicitados
        especialidades_bloqueadas = (
            buscar_especialidades_con_prestaciones(
                db,
                profesional.id,
                ids_a_quitar,
            )
        )

        if especialidades_bloqueadas:
            raise EspecialidadesConPrestacionesError(
                sorted(
                    especialidad.nombre
                    for especialidad
                    in especialidades_bloqueadas
                )
            )

    profesional_actualizado = actualizar_profesional(
        profesional,
        datos,
    )

    if especialidades is not None:
        profesional_actualizado = (
            reemplazar_especialidades_profesional(
                profesional_actualizado,
                datos.especialidades,
                especialidades,
            )
        )

    try:
        db.commit()
        db.refresh(profesional_actualizado)

    except IntegrityError:
        db.rollback()
        raise

    return profesional_actualizado


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
