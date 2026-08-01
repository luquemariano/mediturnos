from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import obtener_db
from app.schemas.paciente import (
    PacienteCrear,
    PacienteRespuesta,
)
from app.services.paciente_service import (
    crear_paciente,
    obtener_paciente_por_id,
    obtener_pacientes,
)


router = APIRouter(
    prefix="/pacientes",
    tags=["Pacientes"],
)


@router.post(
    "/",
    response_model=PacienteRespuesta,
    status_code=201,
    summary="Registrar un paciente",
)
def registrar_paciente(
    datos: PacienteCrear,
    db: Session = Depends(obtener_db),
):
    try:
        return crear_paciente(db, datos)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un paciente con ese DNI.",
        )


@router.get(
    "/",
    response_model=list[PacienteRespuesta],
    summary="Listar pacientes",
)
def listar_pacientes(
    db: Session = Depends(obtener_db),
):
    return obtener_pacientes(db)


@router.get(
    "/{paciente_id}",
    response_model=PacienteRespuesta,
    summary="Consultar un paciente",
)
def ver_paciente(
    paciente_id: int,
    db: Session = Depends(obtener_db),
):
    paciente = obtener_paciente_por_id(db, paciente_id)

    if paciente is None:
        raise HTTPException(
            status_code=404,
            detail="Paciente no encontrado.",
        )

    return paciente