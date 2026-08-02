from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import generar_hash_password
from app.models.usuario import Usuario
from app.repositories.usuario_repository import (
    buscar_usuario_por_email,
    guardar_usuario,
    listar_usuarios,
)
from app.schemas.usuario import UsuarioCrear


def crear_usuario(
    db: Session,
    datos: UsuarioCrear,
) -> Usuario:
    usuario_existente = buscar_usuario_por_email(
        db,
        datos.email,
    )

    if usuario_existente is not None:
        raise HTTPException(
            status_code=409,
            detail="Ya existe un usuario con ese email.",
        )

    usuario = Usuario(
        nombre=datos.nombre,
        email=datos.email,
        password_hash=generar_hash_password(
            datos.password
        ),
        rol=datos.rol,
    )

    guardar_usuario(
        db,
        usuario,
    )

    try:
        db.commit()
        db.refresh(usuario)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Ya existe un usuario con ese email.",
        )

    return usuario


def obtener_usuarios(
    db: Session,
) -> list[Usuario]:
    return listar_usuarios(db)