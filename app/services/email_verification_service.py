from datetime import UTC, datetime, timedelta
import hashlib
import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.email_verification_token import EmailVerificationToken
from app.models.usuario import Usuario
from app.repositories.email_verification_repository import (
    buscar_por_hash,
    crear_token,
    invalidar_tokens_activos,
)


EMAIL_VERIFICATION_EXPIRE_HOURS = 24

MENSAJE_TOKEN_INVALIDO = (
    "El enlace de verificación no es válido o venció."
)


def _hash_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def generar_token_verificacion(
    db: Session,
    usuario: Usuario,
) -> str:
    ahora = datetime.now(UTC)

    token_plano = secrets.token_urlsafe(32)

    invalidar_tokens_activos(
        db,
        usuario.id,
        ahora,
    )

    crear_token(
        db,
        EmailVerificationToken(
            usuario_id=usuario.id,
            token_hash=_hash_token(token_plano),
            expires_at=ahora
            + timedelta(hours=EMAIL_VERIFICATION_EXPIRE_HOURS),
            created_at=ahora,
        ),
    )

    return token_plano


def verificar_email(
    db: Session,
    token: str,
) -> Usuario:
    registro = buscar_por_hash(
        db,
        _hash_token(token),
    )

    ahora = datetime.now(UTC)

    if registro is None or registro.used_at is not None:
        raise HTTPException(
            status_code=400,
            detail=MENSAJE_TOKEN_INVALIDO,
        )

    expira = registro.expires_at

    if expira.tzinfo is None:
        expira = expira.replace(tzinfo=UTC)

    if expira <= ahora:
        raise HTTPException(
            status_code=400,
            detail=MENSAJE_TOKEN_INVALIDO,
        )

    usuario = registro.usuario

    usuario.email_verificado = True
    usuario.email_verificado_en = ahora

    invalidar_tokens_activos(
        db,
        usuario.id,
        ahora,
    )

    try:
        db.commit()
        db.refresh(usuario)
    except Exception:
        db.rollback()
        raise

    return usuario