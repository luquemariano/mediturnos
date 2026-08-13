from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import (
    obtener_usuario_actual,
    requiere_roles,
)
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.paciente import PacienteSeleccionRespuesta
from app.schemas.profesional import (
    ProfesionalActualizar,
    ProfesionalCrear,
    ProfesionalRespuesta,
)
from app.schemas.turno import (
    TurnoCrearProfesional,
    TurnoReprogramar,
    TurnoRespuesta,
)
from app.schemas.disponibilidad import (
    DisponibilidadActualizar,
    DisponibilidadRespuesta,
)
from app.schemas.disponibilidad_excepcion import (
    DisponibilidadExcepcionCrear,
    DisponibilidadExcepcionRespuesta,
    DisponibilidadExcepcionRango,
    DisponibilidadExcepcionRangoCreadoRespuesta,
    DisponibilidadExcepcionRangoReabiertoRespuesta,
    FeriadoCrear,
)
from app.services.paciente_service import obtener_pacientes_activos
from app.services.profesional_service import (
    EspecialidadesConPrestacionesError,
    EspecialidadesDuplicadasError,
    EspecialidadesInvalidasError,
    crear_profesional,
    modificar_profesional,
    obtener_mi_profesional,
    obtener_profesional_por_id,
    obtener_profesionales,
)
from app.services.turno_service import (
    cancelar_turno_profesional,
    crear_turno_profesional,
    obtener_agenda_de_profesional,
    reprogramar_turno_profesional,
)
from app.services.disponibilidad_service import (
    actualizar_disponibilidad_profesional,
    desactivar_disponibilidad_profesional,
)
from app.services.disponibilidad_excepcion_service import (
    crear_excepcion,
    eliminar_excepcion,
    obtener_excepciones,
    cerrar_rango,
    reabrir_rango,
    crear_feriado,
    eliminar_feriado,
)
from datetime import date


router = APIRouter(
    prefix="/profesionales",
    tags=["Profesionales"],
)


@router.post(
    "/",
    response_model=ProfesionalRespuesta,
    status_code=201,
    summary="Crear profesional",
)
def registrar_profesional(
    datos: ProfesionalCrear,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        requiere_roles("administrador")
    ),
):
    try:
        return crear_profesional(
            db,
            datos,
        )

    except EspecialidadesDuplicadasError:
        raise HTTPException(
            status_code=400,
            detail="No se puede repetir una especialidad.",
        )

    except EspecialidadesInvalidasError:
        raise HTTPException(
            status_code=400,
            detail="Una o más especialidades no existen.",
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Ya existe un profesional con esa matrícula.",
        )


@router.get(
    "/me",
    response_model=ProfesionalRespuesta,
    summary="Consultar mi perfil profesional",
)
def ver_mi_perfil_profesional(
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        obtener_usuario_actual
    ),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(
            status_code=403,
            detail="El usuario autenticado no es un profesional.",
        )

    return obtener_mi_profesional(
        db,
        usuario_actual.id,
    )


@router.get(
    "/me/agenda",
    response_model=list[TurnoRespuesta],
    summary="Consultar mi agenda profesional",
)
def ver_mi_agenda(
    estado: str | None = None,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        obtener_usuario_actual
    ),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(
            status_code=403,
            detail="El usuario autenticado no es un profesional.",
        )

    profesional = obtener_mi_profesional(
        db,
        usuario_actual.id,
    )

    return obtener_agenda_de_profesional(
        db,
        profesional.id,
        estado,
    )


@router.get(
    "/me/pacientes",
    response_model=list[PacienteSeleccionRespuesta],
    summary="Listar pacientes activos para mi agenda",
)
def listar_pacientes_para_mi_agenda(
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(
            status_code=403,
            detail="El usuario autenticado no es un profesional.",
        )

    obtener_mi_profesional(db, usuario_actual.id)
    return obtener_pacientes_activos(db)


@router.post(
    "/me/turnos",
    response_model=TurnoRespuesta,
    status_code=201,
    summary="Crear un turno en mi agenda profesional",
)
def crear_turno_en_mi_agenda(
    datos: TurnoCrearProfesional,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(
            status_code=403,
            detail="El usuario autenticado no es un profesional.",
        )

    profesional = obtener_mi_profesional(db, usuario_actual.id)
    return crear_turno_profesional(db, profesional.id, datos)


@router.patch(
    "/me/disponibilidades/{disponibilidad_id}",
    response_model=DisponibilidadRespuesta,
    summary="Actualizar una disponibilidad habitual propia",
)
def actualizar_mi_disponibilidad(
    disponibilidad_id: int,
    datos: DisponibilidadActualizar,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(status_code=403, detail="El usuario autenticado no es un profesional.")
    profesional = obtener_mi_profesional(db, usuario_actual.id)
    return actualizar_disponibilidad_profesional(
        db, disponibilidad_id, profesional.id, datos,
    )


@router.delete(
    "/me/disponibilidades/{disponibilidad_id}",
    response_model=DisponibilidadRespuesta,
    summary="Eliminar una disponibilidad habitual propia",
)
def eliminar_mi_disponibilidad(
    disponibilidad_id: int,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(status_code=403, detail="El usuario autenticado no es un profesional.")
    profesional = obtener_mi_profesional(db, usuario_actual.id)
    return desactivar_disponibilidad_profesional(
        db, disponibilidad_id, profesional.id,
    )


@router.get(
    "/me/excepciones-disponibilidad",
    response_model=list[DisponibilidadExcepcionRespuesta],
    summary="Listar mis excepciones de disponibilidad",
)
def listar_mis_excepciones_disponibilidad(
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(status_code=403, detail="El usuario autenticado no es un profesional.")
    profesional = obtener_mi_profesional(db, usuario_actual.id)
    return obtener_excepciones(db, profesional.id, fecha_desde, fecha_hasta)


@router.post(
    "/me/excepciones-disponibilidad",
    response_model=DisponibilidadExcepcionRespuesta,
    status_code=201,
    summary="Crear una excepción de disponibilidad propia",
)
def crear_mi_excepcion_disponibilidad(
    datos: DisponibilidadExcepcionCrear,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(status_code=403, detail="El usuario autenticado no es un profesional.")
    profesional = obtener_mi_profesional(db, usuario_actual.id)
    return crear_excepcion(db, profesional.id, datos)


@router.post(
    "/me/excepciones-disponibilidad/rango",
    response_model=DisponibilidadExcepcionRangoCreadoRespuesta,
    summary="Cerrar un rango de fechas propio",
)
def cerrar_mi_disponibilidad_por_rango(
    datos: DisponibilidadExcepcionRango,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(status_code=403, detail="El usuario autenticado no es un profesional.")
    profesional = obtener_mi_profesional(db, usuario_actual.id)
    return cerrar_rango(db, profesional.id, datos.fecha_desde, datos.fecha_hasta)


@router.post(
    "/me/excepciones-disponibilidad/reabrir-rango",
    response_model=DisponibilidadExcepcionRangoReabiertoRespuesta,
    summary="Reabrir un rango de fechas propio",
)
def reabrir_mi_disponibilidad_por_rango(
    datos: DisponibilidadExcepcionRango,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(status_code=403, detail="El usuario autenticado no es un profesional.")
    profesional = obtener_mi_profesional(db, usuario_actual.id)
    return reabrir_rango(db, profesional.id, datos.fecha_desde, datos.fecha_hasta)


@router.delete(
    "/me/excepciones-disponibilidad/{excepcion_id}",
    response_model=DisponibilidadExcepcionRespuesta,
    summary="Eliminar una excepción de disponibilidad propia",
)
def eliminar_mi_excepcion_disponibilidad(
    excepcion_id: int,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(status_code=403, detail="El usuario autenticado no es un profesional.")
    profesional = obtener_mi_profesional(db, usuario_actual.id)
    return eliminar_excepcion(db, profesional.id, excepcion_id)


@router.post(
    "/me/feriados",
    response_model=DisponibilidadExcepcionRespuesta,
    status_code=201,
    summary="Agregar un feriado o día no laborable propio",
)
def crear_mi_feriado(
    datos: FeriadoCrear,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(status_code=403, detail="El usuario autenticado no es un profesional.")
    profesional = obtener_mi_profesional(db, usuario_actual.id)
    return crear_feriado(db, profesional.id, datos)


@router.delete(
    "/me/feriados/{excepcion_id}",
    response_model=DisponibilidadExcepcionRespuesta,
    summary="Quitar un feriado o día no laborable propio",
)
def eliminar_mi_feriado(
    excepcion_id: int,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(status_code=403, detail="El usuario autenticado no es un profesional.")
    profesional = obtener_mi_profesional(db, usuario_actual.id)
    return eliminar_feriado(db, profesional.id, excepcion_id)


@router.patch(
    "/me/agenda/{turno_id}/cancelar",
    response_model=TurnoRespuesta,
    summary="Cancelar un turno de mi agenda",
)
def cancelar_turno_de_mi_agenda(
    turno_id: int,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(
            status_code=403,
            detail="El usuario autenticado no es un profesional.",
        )

    profesional = obtener_mi_profesional(db, usuario_actual.id)
    return cancelar_turno_profesional(
        db,
        turno_id,
        profesional.id,
    )


@router.patch(
    "/me/agenda/{turno_id}/reprogramar",
    response_model=TurnoRespuesta,
    summary="Reprogramar un turno de mi agenda",
)
def reprogramar_turno_de_mi_agenda(
    turno_id: int,
    datos: TurnoReprogramar,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(
            status_code=403,
            detail="El usuario autenticado no es un profesional.",
        )

    profesional = obtener_mi_profesional(db, usuario_actual.id)
    return reprogramar_turno_profesional(
        db,
        turno_id,
        profesional.id,
        datos,
    )
@router.get(
    "/",
    response_model=list[ProfesionalRespuesta],
    summary="Listar profesionales",
)
def listar_profesionales(
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        requiere_roles(
            "administrador",
            "recepcionista",
            "profesional",
            "paciente",
        )
    ),
):
    return obtener_profesionales(db)

from app.services.turno_service import (
    finalizar_turno_profesional,
    marcar_ausente_turno_profesional,
    obtener_agenda_de_profesional,
)

@router.patch(
    "/me/agenda/{turno_id}/finalizar",
    response_model=TurnoRespuesta,
    summary="Finalizar un turno de mi agenda",
)
def finalizar_mi_turno(
    turno_id: int,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        obtener_usuario_actual
    ),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(
            status_code=403,
            detail="El usuario autenticado no es un profesional.",
        )

    profesional = obtener_mi_profesional(
        db,
        usuario_actual.id,
    )

    return finalizar_turno_profesional(
        db,
        turno_id,
        profesional.id,
    )


@router.patch(
    "/me/agenda/{turno_id}/ausente",
    response_model=TurnoRespuesta,
    summary="Marcar ausente en un turno de mi agenda",
)
def marcar_ausente_mi_turno(
    turno_id: int,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        obtener_usuario_actual
    ),
):
    if usuario_actual.rol != "profesional":
        raise HTTPException(
            status_code=403,
            detail="El usuario autenticado no es un profesional.",
        )

    profesional = obtener_mi_profesional(
        db,
        usuario_actual.id,
    )

    return marcar_ausente_turno_profesional(
        db,
        turno_id,
        profesional.id,
    )

@router.get(
    "/{profesional_id}",
    response_model=ProfesionalRespuesta,
    summary="Consultar un profesional",
)
def ver_profesional(
    profesional_id: int,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        requiere_roles(
            "administrador",
            "recepcionista",
            "profesional",
            "paciente",
        )
    ),
):
    profesional = obtener_profesional_por_id(
        db,
        profesional_id,
    )

    if profesional is None:
        raise HTTPException(
            status_code=404,
            detail="Profesional no encontrado.",
        )

    return profesional


@router.patch(
    "/{profesional_id}",
    response_model=ProfesionalRespuesta,
    summary="Actualizar un profesional",
)
def actualizar_profesional(
    profesional_id: int,
    datos: ProfesionalActualizar,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        requiere_roles("administrador")
    ),
):
    profesional = obtener_profesional_por_id(
        db,
        profesional_id,
    )

    if profesional is None:
        raise HTTPException(
            status_code=404,
            detail="Profesional no encontrado.",
        )

    try:
        return modificar_profesional(
            db,
            profesional,
            datos,
        )

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=(
                "Ya existe un profesional con esa matrícula."
            ),
        )

    except EspecialidadesDuplicadasError:
        raise HTTPException(
            status_code=400,
            detail="No se puede repetir una especialidad.",
        )

    except EspecialidadesInvalidasError:
        raise HTTPException(
            status_code=400,
            detail="Una o más especialidades no existen.",
        )

    except EspecialidadesConPrestacionesError as error:
        nombres = ", ".join(error.nombres)

        raise HTTPException(
            status_code=409,
            detail=(
                "No se puede quitar la especialidad "
                f"'{nombres}' porque tiene prestaciones "
                "asociadas a este profesional."
            ),
        )
