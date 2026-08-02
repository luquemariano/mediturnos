from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import requiere_roles
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.usuario import (
    UsuarioCrear,
    UsuarioRespuesta,
)
from app.services.usuario_service import (
    crear_usuario,
    obtener_usuarios,
)


router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"],
)


@router.post(
    "/",
    response_model=UsuarioRespuesta,
    status_code=201,
    summary="Registrar usuario",
)
def registrar_usuario(
    datos: UsuarioCrear,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
    requiere_roles("administrador"),
)
):
    return crear_usuario(
        db,
        datos,
    )


@router.get(
    "/",
    response_model=list[UsuarioRespuesta],
    summary="Listar usuarios",
)
def listar_usuarios(
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(
    requiere_roles("administrador"),
)
):
    return obtener_usuarios(db)