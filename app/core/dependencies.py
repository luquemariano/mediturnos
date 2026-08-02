import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.jwt import verificar_access_token
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.repositories.usuario_repository import buscar_usuario_por_id
from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session


bearer_scheme = HTTPBearer()


def obtener_usuario_actual(
    credenciales: HTTPAuthorizationCredentials = Depends(
        bearer_scheme,
    ),
    db: Session = Depends(obtener_db),
) -> Usuario:
    credenciales_invalidas = HTTPException(
        status_code=401,
        detail="No se pudieron validar las credenciales.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    token = credenciales.credentials
    print("TOKEN RECIBIDO:", token)

    try:
        payload = verificar_access_token(token)
        print("PAYLOAD:", payload)

        usuario_id = payload.get("sub")

        if usuario_id is None:
            raise credenciales_invalidas

        usuario_id = int(usuario_id)

    except (
        jwt.ExpiredSignatureError,
        jwt.InvalidTokenError,
        ValueError,
    ):
        raise credenciales_invalidas

    usuario = buscar_usuario_por_id(
        db,
        usuario_id,
    )

    if usuario is None:
        raise credenciales_invalidas

    if not usuario.activo:
        raise HTTPException(
            status_code=403,
            detail="El usuario se encuentra inactivo.",
        )

    return usuario


def requiere_administrador(
    usuario: Usuario = Depends(
        obtener_usuario_actual,
    ),
) -> Usuario:
    if usuario.rol != "administrador":
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes.",
        )

    return usuario


def requiere_profesional(
    usuario: Usuario = Depends(
        obtener_usuario_actual,
    ),
) -> Usuario:
    if usuario.rol != "profesional":
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes.",
        )

    return usuario


def requiere_recepcionista(
    usuario: Usuario = Depends(
        obtener_usuario_actual,
    ),
) -> Usuario:
    if usuario.rol != "recepcionista":
        raise HTTPException(
            status_code=403,
            detail="Permisos insuficientes.",
        )

    return usuario



def requiere_roles(
    *roles_permitidos: str,
) -> Callable:
    def validar_rol(
        usuario: Usuario = Depends(
            obtener_usuario_actual,
        ),
    ) -> Usuario:
        if usuario.rol not in roles_permitidos:
            raise HTTPException(
                status_code=403,
                detail="Permisos insuficientes.",
            )

        return usuario

    return validar_rol