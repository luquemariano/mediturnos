from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import (
    obtener_usuario_actual,
    requiere_roles,
)
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.profesional import (
    ProfesionalActualizar,
    ProfesionalCrear,
    ProfesionalRespuesta,
)
from app.schemas.turno import TurnoRespuesta
from app.services.profesional_service import (
    EspecialidadesDuplicadasError,
    EspecialidadesInvalidasError,
    crear_profesional,
    modificar_profesional,
    obtener_mi_profesional,
    obtener_profesional_por_id,
    obtener_profesionales,
)
from app.services.turno_service import obtener_agenda_de_profesional


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
    summary="Actualizar datos básicos de un profesional",
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
