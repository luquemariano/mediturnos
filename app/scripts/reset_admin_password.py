"""Reset puntual y explícito de la contraseña de un administrador global.

Uso desde Render Shell, con las variables temporales configuradas en la sesión:

    python -m app.scripts.reset_admin_password

La contraseña nunca se acepta por argumentos ni se incluye en mensajes.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable, Mapping

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import generar_hash_password
from app.database.connection import SessionLocal
from app.models.usuario import Usuario


class ResetAdminError(RuntimeError):
    """Error seguro y esperado del procedimiento administrativo."""


class AdminNoEncontradoError(ResetAdminError):
    pass


class UsuarioNoAdministradorError(ResetAdminError):
    pass


def _normalizar_email(valor: str | None) -> str:
    return (valor or "").strip().casefold()


def resetear_password_admin(
    db: Session,
    *,
    email: str | None,
    password: str | None,
    generar_hash: Callable[[str], str] | None = None,
) -> Usuario:
    """Actualiza únicamente el hash del administrador identificado."""
    email_normalizado = _normalizar_email(email)
    if not email_normalizado:
        raise ResetAdminError("RESET_ADMIN_EMAIL es obligatorio.")
    if not password:
        raise ResetAdminError("RESET_ADMIN_PASSWORD es obligatorio.")
    if len(password) < 12:
        raise ResetAdminError("La contraseña debe tener al menos 12 caracteres.")

    try:
        usuario = (
            db.query(Usuario)
            .filter(func.lower(Usuario.email) == email_normalizado)
            .one_or_none()
        )
        if usuario is None:
            raise AdminNoEncontradoError("No existe un usuario con ese email.")
        if usuario.rol != "administrador":
            raise UsuarioNoAdministradorError("El usuario identificado no es administrador global.")

        usuario.password_hash = (generar_hash or generar_hash_password)(password)
        db.flush()
        db.commit()
        return usuario
    except ResetAdminError:
        try:
            db.rollback()
        except SQLAlchemyError:
            pass
        raise
    except SQLAlchemyError:
        try:
            db.rollback()
        except SQLAlchemyError:
            pass
        raise ResetAdminError("No se pudo completar el reset de contraseña.") from None
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        raise ResetAdminError("No se pudo completar el reset de contraseña.") from None


def main(
    *,
    environ: Mapping[str, str] | None = None,
    session_factory: Callable[[], Session] = SessionLocal,
    output: Callable[[str], object] = print,
) -> int:
    """Ejecuta el procedimiento y devuelve un código de salida seguro."""
    variables = environ if environ is not None else os.environ
    db: Session | None = None
    try:
        db = session_factory()
        resetear_password_admin(
            db,
            email=variables.get("RESET_ADMIN_EMAIL"),
            password=variables.get("RESET_ADMIN_PASSWORD"),
        )
        output("Contraseña del administrador actualizada correctamente.")
        return 0
    except ResetAdminError as error:
        output(f"Error: {error}")
        return 1
    except Exception:
        output("Error: no se pudo completar el reset de contraseña.")
        return 1
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    sys.exit(main())
