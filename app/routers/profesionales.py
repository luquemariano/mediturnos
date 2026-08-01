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
    EspecialidadesDuplicadasError,
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
        raise HTTPException(
            status_code=409,
            detail="Ya existe un profesional con esa matrícula.",
        )