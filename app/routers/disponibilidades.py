from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import requiere_roles
from app.database.connection import obtener_db
from app.models.usuario import Usuario
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
from app.services.profesional_service import obtener_mi_profesional
from datetime import date

router = APIRouter(
    prefix="/disponibilidades",
    tags=["Disponibilidades"],
)


def validar_gestion_disponibilidad(
    db: Session,
    usuario_actual: Usuario,
    profesional_id: int,
) -> None:
    if usuario_actual.rol in {
        "administrador",
        "recepcionista",
    }:
        return

    profesional = obtener_mi_profesional(
        db,
        usuario_actual.id,
    )

    if profesional.id != profesional_id:
        raise HTTPException(
            status_code=403,
            detail=(
                "No tiene permisos para gestionar la "
                "disponibilidad de otro profesional."
            ),
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
    usuario_actual: Usuario = Depends(
        requiere_roles(
            "administrador",
            "recepcionista",
            "profesional",
        )
    ),
):
    validar_gestion_disponibilidad(
        db,
        usuario_actual,
        datos.profesional_id,
    )

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
    usuario_actual: Usuario = Depends(
        requiere_roles(
            "administrador",
            "recepcionista",
        )
    ),
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
    usuario_actual: Usuario = Depends(
        requiere_roles(
            "administrador",
            "recepcionista",
            "profesional",
        )
    ),
):
    validar_gestion_disponibilidad(
        db,
        usuario_actual,
        profesional_id,
    )

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
    turno_id_excluido: int | None = None,
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
    if (
        turno_id_excluido is not None
        and usuario_actual.rol not in {
            "administrador",
            "recepcionista",
        }
    ):
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes.",
        )

    return obtener_horarios_libres(
        db,
        prestacion_id,
        fecha,
        turno_id_excluido,
    )
