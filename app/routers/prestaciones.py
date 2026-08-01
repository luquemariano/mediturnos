from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import obtener_db
from app.schemas.prestacion import (
    PrestacionActualizar,
    PrestacionCrear,
    PrestacionRespuesta,
)
from app.services.prestacion_service import (
    crear_prestacion,
    desactivar_prestacion,
    modificar_prestacion,
    obtener_prestacion,
    obtener_prestaciones,
)

router = APIRouter(
    prefix="/prestaciones",
    tags=["Prestaciones"],
)


@router.post(
    "/",
    response_model=PrestacionRespuesta,
    status_code=201,
    summary="Crear una prestación",
    description=(
        "Crea una prestación médica asociada a un profesional "
        "y a una especialidad que tenga asignada."
    ),
)
def registrar_prestacion(
    datos: PrestacionCrear,
    db: Session = Depends(obtener_db),
):
    return crear_prestacion(
        db,
        datos,
    )


@router.get(
    "/",
    response_model=list[PrestacionRespuesta],
    summary="Listar prestaciones",
    description="Devuelve todas las prestaciones registradas.",
)
def listar_prestaciones(
    db: Session = Depends(obtener_db),
):
    return obtener_prestaciones(db)


@router.get(
    "/{prestacion_id}",
    response_model=PrestacionRespuesta,
    summary="Consultar una prestación",
    description="Devuelve una prestación según su identificador.",
)
def ver_prestacion(
    prestacion_id: int,
    db: Session = Depends(obtener_db),
):
    return obtener_prestacion(
        db,
        prestacion_id,
    )
    
@router.patch(
    "/{prestacion_id}",
    response_model=PrestacionRespuesta,
    summary="Actualizar una prestación",
)
def actualizar_prestacion(
    prestacion_id: int,
    datos: PrestacionActualizar,
    db: Session = Depends(obtener_db),
):
    return modificar_prestacion(
        db,
        prestacion_id,
        datos,
    )


@router.delete(
    "/{prestacion_id}",
    response_model=PrestacionRespuesta,
    summary="Desactivar una prestación",
)
def eliminar_prestacion(
    prestacion_id: int,
    db: Session = Depends(obtener_db),
):
    return desactivar_prestacion(
        db,
        prestacion_id,
    )