from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.profesional import Profesional
from app.models.especialidad import Especialidad
from app.services.actividad_profesional_service import (
    obtener_actividad_activa,
    validar_datos_de_actividad,
)
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
    actividad, ids = validar_datos_de_actividad(
        db,
        datos.actividad_profesional_id,
        datos.matricula,
        [item.especialidad_id for item in datos.especialidades or []],
        datos.especialidad_id,
    )
    especialidades = buscar_especialidades_por_ids(db, ids)
    activas = {item.id for item in especialidades if item.activa}
    if activas != set(ids):
        raise EspecialidadesInvalidasError

    profesional = guardar_profesional(
        db,
        datos,
        especialidades,
        actividad,
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
    if datos.especialidades is not None:
        ids_enviados = [item.especialidad_id for item in datos.especialidades]
        if len(ids_enviados) != len(set(ids_enviados)):
            raise EspecialidadesDuplicadasError
    actividad_id = datos.actividad_profesional_id or profesional.actividad_profesional_id
    actividad_cambiada = (
        datos.actividad_profesional_id is not None
        and datos.actividad_profesional_id != profesional.actividad_profesional_id
    )
    asignaciones = datos.especialidades
    especialidades = None

    if actividad_id is not None:
        actividad_actual = profesional.actividad_profesional
        if datos.actividad_profesional_id is not None:
            matricula_validada = (
                datos.matricula
                if "matricula" in datos.model_fields_set
                else profesional.matricula if not actividad_cambiada else None
            )
        elif "matricula" in datos.model_fields_set:
            matricula_validada = datos.matricula
        else:
            matricula_validada = (
                profesional.matricula
                if actividad_actual and actividad_actual.requiere_matricula
                else None
            )

        # Resolve policy and specialty IDs from the trusted catalog; never from client flags.
        actividad = obtener_actividad_activa(db, actividad_id)
        if actividad_cambiada and actividad.requiere_matricula and "matricula" not in datos.model_fields_set:
            raise HTTPException(status_code=422, detail="Ingresá una matrícula para la actividad seleccionada.")
        if actividad_cambiada and not actividad.requiere_matricula:
            if "matricula" not in datos.model_fields_set or datos.matricula is not None:
                raise HTTPException(
                    status_code=422,
                    detail="Confirmá que la actividad no requiere matrícula quitando el valor actual.",
                )
        if datos.especialidades is not None:
            ids_solicitados = [item.especialidad_id for item in datos.especialidades]
        elif actividad_cambiada and not actividad.requiere_especialidad:
            # Non-specialty activities use the server-configured service category.
            ids_solicitados = []
        else:
            ids_solicitados = [item.especialidad_id for item in profesional.especialidades_asignadas]
        _, ids_finales = validar_datos_de_actividad(
            db,
            actividad_id,
            matricula_validada,
            ids_solicitados,
        )
        especialidades = buscar_especialidades_por_ids(db, ids_finales)
        activas = {item.id for item in especialidades if item.activa}
        if activas != set(ids_finales):
            raise EspecialidadesInvalidasError

        if datos.especialidades is None and (
            actividad_cambiada or set(ids_finales) != set(ids_solicitados)
        ):
            relaciones_actuales = {
                relacion.especialidad_id: relacion
                for relacion in profesional.especialidades_asignadas
            }
            asignaciones = [
                EspecialidadProfesionalCrear(
                    especialidad_id=especialidad.id,
                    duracion_turno_minutos=(
                        relaciones_actuales[especialidad.id].duracion_turno_minutos
                        or especialidad.duracion_turno_minutos
                        if especialidad.id in relaciones_actuales
                        else especialidad.duracion_turno_minutos
                    ),
                )
                for especialidad in especialidades
            ]
    elif "matricula" in datos.model_fields_set and datos.matricula is None:
        raise HTTPException(
            status_code=422,
            detail="No se puede quitar la matrícula de un perfil sin actividad clasificada.",
        )

    if asignaciones is not None and especialidades is None:
        especialidades = validar_especialidades(db, asignaciones)

    if especialidades is not None and asignaciones is not None:
        ids_actuales = {rel.especialidad_id for rel in profesional.especialidades_asignadas}
        ids_solicitados = {item.especialidad_id for item in asignaciones}
        ids_a_quitar = ids_actuales - ids_solicitados
        bloqueadas = buscar_especialidades_con_prestaciones(db, profesional.id, ids_a_quitar)
        if bloqueadas:
            raise EspecialidadesConPrestacionesError(sorted(item.nombre for item in bloqueadas))

    profesional_actualizado = actualizar_profesional(
        profesional,
        datos,
    )

    if especialidades is not None and asignaciones is not None:
        profesional_actualizado = (
            reemplazar_especialidades_profesional(
                profesional_actualizado,
                asignaciones,
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
