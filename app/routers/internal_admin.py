import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import limitar_reset_admin
from app.database.connection import obtener_db
from app.schemas.internal_admin import MensajeInternoRespuesta, ResetAdminPasswordEntrada
from app.scripts.reset_admin_password import (
    AdminNoEncontradoError,
    ResetAdminError,
    UsuarioNoAdministradorError,
    resetear_password_admin,
)


router = APIRouter(prefix="/internal/admin", tags=["Interno"])


def proteger_reset_admin(
    request: Request,
    token_recibido: str | None = Header(default=None, alias="X-Reset-Admin-Token"),
) -> None:
    token_configurado = settings.reset_admin_token
    if token_configurado is None or not token_configurado.get_secret_value():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurso no disponible.")

    limitar_reset_admin(request)
    esperado = token_configurado.get_secret_value()
    if token_recibido is None or not hmac.compare_digest(token_recibido, esperado):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")


@router.post(
    "/reset-password",
    response_model=MensajeInternoRespuesta,
    dependencies=[Depends(proteger_reset_admin)],
)
def reset_password_admin_interno(
    entrada: ResetAdminPasswordEntrada,
    db: Session = Depends(obtener_db),
) -> MensajeInternoRespuesta:
    nueva_password = entrada.new_password.get_secret_value()
    if len(nueva_password) < 12:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="La contraseña no cumple los requisitos de seguridad.",
        )
    try:
        resetear_password_admin(
            db,
            email=str(entrada.email),
            password=nueva_password,
        )
    except AdminNoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se pudo completar la operación.") from None
    except UsuarioNoAdministradorError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se pudo completar la operación.") from None
    except ResetAdminError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo completar la operación.") from None

    return MensajeInternoRespuesta(mensaje="Operación completada correctamente.")
