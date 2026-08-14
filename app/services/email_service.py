import logging

from app.core.config import settings


logger = logging.getLogger("mediturnos.email.development")
development_email_outbox: dict[str, str] = {}


class EmailServiceUnavailable(RuntimeError):
    pass


def enviar_recuperacion_password(email: str, token: str) -> None:
    if settings.app_env not in {"development", "demo", "test"}:
        raise EmailServiceUnavailable(
            "No hay un proveedor de email configurado para recuperación."
        )

    enlace = f"{settings.frontend_url.rstrip('/')}/reset-password?token={token}"
    development_email_outbox[email] = enlace
    logger.info("Enlace de recuperación generado para %s en la salida controlada.", email)
