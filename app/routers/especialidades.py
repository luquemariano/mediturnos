from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import obtener_db
from app.schemas.especialidad import (
    EspecialidadCrear,
    EspecialidadRespuesta,
)
from app.services.especialidad_service import (
    crear_especialidad,
    obtener_especialidades,
)


router = APIRouter(
    prefix="/especialidades",
    tags=["Especialidades"],
)


@router.post(
    "/",
    response_model=EspecialidadRespuesta,
    status_code=201,
)
def registrar_especialidad(
    datos: EspecialidadCrear,
    db: Session = Depends(obtener_db),
):
    try:
        return crear_especialidad(db, datos)

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una especialidad con ese nombre.",
        )


@router.get(
    "/",
    response_model=list[EspecialidadRespuesta],
)
def listar_especialidades(
    db: Session = Depends(obtener_db),
):
    return obtener_especialidades(db)