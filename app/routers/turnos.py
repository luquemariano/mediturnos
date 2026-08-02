from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import requiere_roles
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.turno import (
    TurnoActualizarEstado,
    TurnoCrear,
    TurnoReprogramar,
    TurnoRespuesta,
)
from app.services.turno_service import (
    cambiar_estado_turno,
    crear_turno,
    obtener_turno,
    obtener_turnos,
    reprogramar_turno,
)


router = APIRouter(
    prefix="/turnos",
    tags=["Turnos"],
)


@router.post(
    "/",
    response_model=TurnoRespuesta,
    status_code=201,
    summary="Reservar un turno",
)
def registrar_turno(
    datos: TurnoCrear,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        requiere_roles(
            "administrador",
            "recepcionista",
        )
    ),
):
    return crear_turno(
        db,
        datos,
    )


@router.get(
    "/",
    response_model=list[TurnoRespuesta],
    summary="Listar turnos",
)
def listar_turnos(
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        requiere_roles(
            "administrador",
            "recepcionista",
            "profesional",
        )
    ),
):
    return obtener_turnos(db)


@router.get(
    "/{turno_id}",
    response_model=TurnoRespuesta,
    summary="Consultar un turno",
)
def ver_turno(
    turno_id: int,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        requiere_roles(
            "administrador",
            "recepcionista",
            "profesional",
        )
    ),
):
    return obtener_turno(
        db,
        turno_id,
    )


@router.patch(
    "/{turno_id}/estado",
    response_model=TurnoRespuesta,
    summary="Cambiar estado de un turno",
)
def actualizar_estado_turno(
    turno_id: int,
    datos: TurnoActualizarEstado,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        requiere_roles(
            "administrador",
            "recepcionista",
        )
    ),
):
    return cambiar_estado_turno(
        db,
        turno_id,
        datos,
    )


@router.patch(
    "/{turno_id}/reprogramar",
    response_model=TurnoRespuesta,
    summary="Reprogramar un turno",
)
def mover_turno(
    turno_id: int,
    datos: TurnoReprogramar,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        requiere_roles(
            "administrador",
            "recepcionista",
        )
    ),
):
    return reprogramar_turno(
        db,
        turno_id,
        datos,
    )