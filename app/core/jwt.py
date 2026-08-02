from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import settings


def crear_access_token(
    usuario_id: int,
    email: str,
    rol: str,
) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.jwt_expire_minutes,
    )

    payload = {
        "sub": str(usuario_id),
        "email": email,
        "rol": rol,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def verificar_access_token(
    token: str,
) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[
            settings.jwt_algorithm,
        ],
    )