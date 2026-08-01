from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import obtener_db
from app.schemas.disponibilidad import (
    DisponibilidadCrear,
    DisponibilidadRespuesta,
    HorarioLibreRespuesta,
)
from app.services.disponibilidad_service import (
    crear_disponibilidad,
    obtener_disponibilidades,
    obtener_disponibilidades_profesional,
    obtener_horarios_libres,
)
from datetime import date

router = APIRouter(
    prefix="/disponibilidades",
    tags=["Disponibilidades"],
)


@router.post(
    "/",
    response_model=DisponibilidadRespuesta,
    status_code=201,
    summary="Registrar disponibilidad",
)
def registrar_disponibilidad(
    datos: DisponibilidadCrear,
    db: Session = Depends(obtener_db),
):
    return crear_disponibilidad(
        db,
        datos,
    )


@router.get(
    "/",
    response_model=list[DisponibilidadRespuesta],
    summary="Listar disponibilidades",
)
def listar_disponibilidades(
    db: Session = Depends(obtener_db),
):
    return obtener_disponibilidades(db)


@router.get(
    "/profesional/{profesional_id}",
    response_model=list[DisponibilidadRespuesta],
    summary="Listar disponibilidad de un profesional",
)
def listar_disponibilidad_profesional(
    profesional_id: int,
    db: Session = Depends(obtener_db),
):
    return obtener_disponibilidades_profesional(
        db,
        profesional_id,
    )
    
@router.get(
    "/horarios-libres/",
    response_model=list[HorarioLibreRespuesta],
    summary="Consultar horarios libres",
)
def listar_horarios_libres(
    prestacion_id: int,
    fecha: date,
    db: Session = Depends(obtener_db),
):
    return obtener_horarios_libres(
        db,
        prestacion_id,
        fecha,
    )