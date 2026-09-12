from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import requiere_roles, obtener_usuario_actual
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.services.profesional_service import obtener_mi_profesional
from app.schemas.public_booking import HabilitacionPrestacionActualizar, PrestacionReservaOnlineRespuesta
from app.services.public_booking_service import actualizar_habilitacion_prestacion
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

@router.patch("/{identificador_publico}/reserva-online", response_model=PrestacionReservaOnlineRespuesta)
def actualizar_reserva_online_prestacion(identificador_publico: str, datos: HabilitacionPrestacionActualizar, db: Session = Depends(obtener_db), usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    if usuario_actual.rol != "profesional":
        raise HTTPException(status_code=403, detail="El usuario autenticado no es un profesional.")
    profesional = obtener_mi_profesional(db, usuario_actual.id)
    if not profesional.activo:
        raise HTTPException(status_code=400, detail="El profesional está inactivo.")
    return actualizar_habilitacion_prestacion(db, profesional, identificador_publico, datos)


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
    usuario_actual: Usuario = Depends(
        requiere_roles("administrador")
    ),
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
    usuario_actual: Usuario = Depends(
        requiere_roles(
            "administrador",
            "recepcionista",
            "paciente",
        )
    ),
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
    usuario_actual: Usuario = Depends(
        requiere_roles(
            "administrador",
            "recepcionista",
            "paciente",
        )
    ),
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
    usuario_actual: Usuario = Depends(
        requiere_roles("administrador")
    ),
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
    usuario_actual: Usuario = Depends(
        requiere_roles("administrador")
    ),
):
    return desactivar_prestacion(
        db,
        prestacion_id,
    )
