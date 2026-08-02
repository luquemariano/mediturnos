from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import (
    obtener_usuario_actual,
    requiere_roles,
)
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.paciente import (
    PacienteCrear,
    PacienteRespuesta,
)
from app.schemas.turno import (
    TurnoCrearPropio,
    TurnoRespuesta,
)
from app.services.paciente_service import (
    crear_paciente,
    obtener_mi_paciente,
    obtener_paciente_por_id,
    obtener_pacientes,
)
from app.services.turno_service import (
    cancelar_turno_paciente,
    crear_turno_propio,
    obtener_turnos_de_paciente,
)


router = APIRouter(
    prefix="/pacientes",
    tags=["Pacientes"],
)


@router.post(
    "/",
    response_model=PacienteRespuesta,
    status_code=201,
    summary="Crear paciente",
)
def registrar_paciente(
    datos: PacienteCrear,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        requiere_roles(
            "administrador",
            "recepcionista",
        )
    ),
):
    try:
        return crear_paciente(
            db,
            datos,
        )

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Ya existe un paciente con ese DNI.",
        )


@router.get(
    "/me",
    response_model=PacienteRespuesta,
    summary="Consultar mi perfil de paciente",
)
def ver_mi_perfil_paciente(
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        obtener_usuario_actual
    ),
):
    if usuario_actual.rol != "paciente":
        raise HTTPException(
            status_code=403,
            detail="El usuario autenticado no es un paciente.",
        )

    return obtener_mi_paciente(
        db,
        usuario_actual.id,
    )


@router.get(
    "/me/turnos",
    response_model=list[TurnoRespuesta],
    summary="Consultar mis turnos",
)
def ver_mis_turnos(
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        obtener_usuario_actual
    ),
):
    if usuario_actual.rol != "paciente":
        raise HTTPException(
            status_code=403,
            detail="El usuario autenticado no es un paciente.",
        )

    paciente = obtener_mi_paciente(
        db,
        usuario_actual.id,
    )

    return obtener_turnos_de_paciente(
        db,
        paciente.id,
    )

@router.post(
    "/me/turnos",
    response_model=TurnoRespuesta,
    status_code=201,
    summary="Reservar mi turno",
)
def reservar_mi_turno(
    datos: TurnoCrearPropio,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        obtener_usuario_actual
    ),
):
    if usuario_actual.rol != "paciente":
        raise HTTPException(
            status_code=403,
            detail="El usuario autenticado no es un paciente.",
        )

    paciente = obtener_mi_paciente(
        db,
        usuario_actual.id,
    )

    return crear_turno_propio(
        db,
        paciente.id,
        datos,
    )

@router.patch(
    "/me/turnos/{turno_id}/cancelar",
    response_model=TurnoRespuesta,
    summary="Cancelar uno de mis turnos",
)
def cancelar_mi_turno(
    turno_id: int,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        obtener_usuario_actual
    ),
):
    if usuario_actual.rol != "paciente":
        raise HTTPException(
            status_code=403,
            detail="El usuario autenticado no es un paciente.",
        )

    paciente = obtener_mi_paciente(
        db,
        usuario_actual.id,
    )

    return cancelar_turno_paciente(
        db,
        turno_id,
        paciente.id,
    )

@router.get(
    "/",
    response_model=list[PacienteRespuesta],
    summary="Listar pacientes",
)
def listar_pacientes(
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        requiere_roles(
            "administrador",
            "recepcionista",
            "profesional",
        )
    ),
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
    usuario_actual: Usuario = Depends(
        requiere_roles(
            "administrador",
            "recepcionista",
            "profesional",
        )
    ),
):
    paciente = obtener_paciente_por_id(
        db,
        paciente_id,
    )

    if paciente is None:
        raise HTTPException(
            status_code=404,
            detail="Paciente no encontrado.",
        )

    return paciente