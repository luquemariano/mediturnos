from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import obtener_db
from app.schemas.auth import (
    ChangePasswordDatos, ForgotPasswordDatos, LoginDatos, MensajeRespuesta,
    ResetPasswordDatos, TokenRespuesta,
)
from app.services.auth_service import (
    MENSAJE_FORGOT, autenticar_usuario, cambiar_password, resetear_password,
    solicitar_reset_password,
)
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


@router.post("/forgot-password", response_model=MensajeRespuesta)
def forgot_password(datos: ForgotPasswordDatos, db: Session = Depends(obtener_db)):
    solicitar_reset_password(db, datos.email)
    return MensajeRespuesta(mensaje=MENSAJE_FORGOT)


@router.post("/reset-password", response_model=MensajeRespuesta)
def reset_password(datos: ResetPasswordDatos, db: Session = Depends(obtener_db)):
    resetear_password(db, datos.token, datos.new_password)
    return MensajeRespuesta(mensaje="Tu contraseña fue actualizada.")


@router.post("/change-password", response_model=MensajeRespuesta)
def change_password(
    datos: ChangePasswordDatos,
    db: Session = Depends(obtener_db),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
):
    cambiar_password(db, usuario_actual, datos.current_password, datos.new_password)
    return MensajeRespuesta(mensaje="Tu contraseña fue actualizada.")
