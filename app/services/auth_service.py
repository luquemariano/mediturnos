from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.jwt import crear_access_token
from app.core.security import verificar_password
from app.repositories.usuario_repository import buscar_usuario_por_email


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