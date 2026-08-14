from datetime import UTC, datetime, timedelta
import hashlib
import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.jwt import crear_access_token
from app.core.config import settings
from app.core.security import generar_hash_password, verificar_password
from app.models.password_reset_token import PasswordResetToken
from app.models.usuario import Usuario
from app.repositories.password_reset_repository import (
    buscar_por_hash,
    crear_token,
    invalidar_tokens_activos,
)
from app.repositories.usuario_repository import buscar_usuario_por_email
from app.services.email_service import EmailServiceUnavailable, enviar_recuperacion_password


MENSAJE_FORGOT = (
    "Si existe una cuenta asociada a ese correo, recibirás instrucciones "
    "para restablecer tu contraseña."
)
MENSAJE_TOKEN_INVALIDO = "El enlace de recuperación no es válido o venció."


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def solicitar_reset_password(db: Session, email: str) -> str:
    usuario = buscar_usuario_por_email(db, email)
    if usuario is None or not usuario.activo:
        return MENSAJE_FORGOT

    ahora = datetime.now(UTC)
    token_plano = secrets.token_urlsafe(32)
    invalidar_tokens_activos(db, usuario.id, ahora)
    crear_token(db, PasswordResetToken(
        usuario_id=usuario.id,
        token_hash=_hash_token(token_plano),
        expires_at=ahora + timedelta(minutes=settings.password_reset_expire_minutes),
        created_at=ahora,
    ))
    try:
        enviar_recuperacion_password(usuario.email, token_plano)
        db.commit()
    except EmailServiceUnavailable:
        db.rollback()
    except Exception:
        db.rollback()
        raise
    return MENSAJE_FORGOT


def resetear_password(db: Session, token: str, nueva_password: str) -> None:
    registro = buscar_por_hash(db, _hash_token(token))
    ahora = datetime.now(UTC)
    if registro is None or registro.used_at is not None:
        raise HTTPException(status_code=400, detail=MENSAJE_TOKEN_INVALIDO)
    expira = registro.expires_at
    if expira.tzinfo is None:
        expira = expira.replace(tzinfo=UTC)
    if expira <= ahora:
        raise HTTPException(status_code=400, detail=MENSAJE_TOKEN_INVALIDO)

    usuario = registro.usuario
    usuario.password_hash = generar_hash_password(nueva_password)
    invalidar_tokens_activos(db, usuario.id, ahora)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def cambiar_password(
    db: Session, usuario: Usuario, password_actual: str, nueva_password: str
) -> None:
    if not verificar_password(password_actual, usuario.password_hash):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta.")
    if verificar_password(nueva_password, usuario.password_hash):
        raise HTTPException(
            status_code=400,
            detail="La nueva contraseña debe ser diferente de la actual.",
        )
    usuario.password_hash = generar_hash_password(nueva_password)
    invalidar_tokens_activos(db, usuario.id, datetime.now(UTC))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def autenticar_usuario(
    db: Session,
    email: str,
    password: str,
) -> str:
    usuario = buscar_usuario_por_email(
        db,
        email,
    )

    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail="Email o contraseña incorrectos.",
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=403,
            detail="El usuario se encuentra inactivo.",
        )

    password_correcto = verificar_password(
        password,
        usuario.password_hash,
    )

    if not password_correcto:
        raise HTTPException(
            status_code=401,
            detail="Email o contraseña incorrectos.",
        )

    return crear_access_token(
        usuario_id=usuario.id,
        email=usuario.email,
        rol=usuario.rol,
    )
