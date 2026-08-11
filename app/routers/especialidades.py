from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.dependencies import requiere_roles
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.especialidad import (
    EspecialidadActualizar,
    EspecialidadCrear,
    EspecialidadRespuesta,
)
from app.services.especialidad_service import (
    crear_especialidad,
    modificar_especialidad,
    obtener_especialidad_por_id,
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
    usuario_actual: Usuario = Depends(
        requiere_roles("administrador")
    ),
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
    usuario_actual: Usuario = Depends(
        requiere_roles(
            "administrador",
            "recepcionista",
            "profesional",
            "paciente",
        )
    ),
):
    return obtener_especialidades(db)

@router.get(
    "/{especialidad_id}",
    response_model=EspecialidadRespuesta,
)
def ver_especialidad(
    especialidad_id: int,
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
    especialidad = obtener_especialidad_por_id(
        db,
        especialidad_id,
    )

    if especialidad is None:
        raise HTTPException(
            status_code=404,
            detail="La especialidad solicitada no existe.",
        )

    return especialidad

@router.patch(
    "/{especialidad_id}",
    response_model=EspecialidadRespuesta,
)
def actualizar_especialidad(
    especialidad_id: int,
    datos: EspecialidadActualizar,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
        requiere_roles("administrador")
    ),
):
    especialidad = obtener_especialidad_por_id(
        db,
        especialidad_id,
    )

    if especialidad is None:
        raise HTTPException(
            status_code=404,
            detail="La especialidad solicitada no existe.",
        )

    try:
        return modificar_especialidad(
            db,
            especialidad,
            datos,
        )

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una especialidad con ese nombre.",
        )
