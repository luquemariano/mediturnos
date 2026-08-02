from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import obtener_db
from app.schemas.auth import LoginDatos, TokenRespuesta
from app.services.auth_service import autenticar_usuario
from app.core.dependencies import obtener_usuario_actual
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioRespuesta


router = APIRouter(
    prefix="/auth",
    tags=["Autenticación"],
)


@router.post(
    "/login",
    response_model=TokenRespuesta,
    summary="Iniciar sesión",
)
def login(
    datos: LoginDatos,
    db: Session = Depends(obtener_db),
):
    access_token = autenticar_usuario(
        db,
        datos.email,
        datos.password,
    )

    return TokenRespuesta(
        access_token=access_token,
    )
    
@router.get(
    "/me",
    response_model=UsuarioRespuesta,
    summary="Consultar usuario autenticado",
)
def obtener_mi_usuario(
    usuario_actual: Usuario = Depends(
        obtener_usuario_actual
    ),
):
    return usuario_actual