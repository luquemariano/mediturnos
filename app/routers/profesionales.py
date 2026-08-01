from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import obtener_db
from app.schemas.profesional import (
    ProfesionalCrear,
    ProfesionalRespuesta,
)
from app.services.profesional_service import (
    EspecialidadesInvalidasError,
    crear_profesional,
    obtener_profesional_por_id,
    obtener_profesionales,
)


router = APIRouter(
    prefix="/profesionales",
    tags=["Profesionales"],
)


@router.post(
    "/",
    response_model=ProfesionalRespuesta,
    status_code=201,
)
def registrar_profesional(
    datos: ProfesionalCrear,
    db: Session = Depends(obtener_db),
):
    try:
        return crear_profesional(
            db,
            datos,
        )

    except EspecialidadesInvalidasError:
        raise HTTPException(
            status_code=400,
            detail="Una o más especialidades no existen.",
        )

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un profesional con esa matrícula.",
        )


@router.get(
    "/",
    response_model=list[ProfesionalRespuesta],
)
def listar_profesionales(
    db: Session = Depends(obtener_db),
):
    return obtener_profesionales(db)


@router.get(
    "/{profesional_id}",
    response_model=ProfesionalRespuesta,
)
def ver_profesional(
    profesional_id: int,
    db: Session = Depends(obtener_db),
):
    profesional = obtener_profesional_por_id(
        db,
        profesional_id,
    )

    if profesional is None:
        raise HTTPException(
            status_code=404,
            detail="El profesional solicitado no existe.",
        )

    return profesional