from dataclasses import dataclass
from html import escape
import logging
from typing import Protocol
from urllib.parse import urlencode

import requests

from app.core.config import settings


logger = logging.getLogger("mediturnos.email")
development_email_outbox: dict[str, str] = {}
RESEND_API_URL = "https://api.resend.com/emails"
RESEND_TIMEOUT_SECONDS = 10


class EmailDeliveryError(RuntimeError):
    """Error sanitizado al entregar un email transaccional."""


class EmailServiceUnavailable(EmailDeliveryError):
    pass


@dataclass(frozen=True)
class TransactionalEmail:
    destinatario: str
    asunto: str
    html: str
    texto: str


class EmailProvider(Protocol):
    def enviar(self, email: TransactionalEmail) -> None: ...


class InMemoryEmailProvider:
    def enviar(self, email: TransactionalEmail) -> None:
        development_email_outbox[email.destinatario] = email.texto
        logger.info("Email transaccional generado en la salida local controlada.")


class ResendEmailProvider:
    def __init__(self, api_key: str, remitente: str) -> None:
        self._api_key = api_key
        self._remitente = remitente

    def enviar(self, email: TransactionalEmail) -> None:
        try:
            respuesta = requests.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": self._remitente,
                    "to": [email.destinatario],
                    "subject": email.asunto,
                    "html": email.html,
                    "text": email.texto,
                },
                timeout=RESEND_TIMEOUT_SECONDS,
            )
        except requests.RequestException as error:
            raise EmailDeliveryError(
                "El proveedor de email no está disponible."
            ) from error

        if not 200 <= respuesta.status_code < 300:
            raise EmailDeliveryError(
                "El proveedor de email rechazó la entrega."
            )


def obtener_email_provider() -> EmailProvider:
    if settings.email_provider == "resend":
        if settings.resend_api_key is None or not settings.email_from:
            raise EmailServiceUnavailable(
                "El proveedor de email no está configurado."
            )
        return ResendEmailProvider(
            settings.resend_api_key.get_secret_value(),
            settings.email_from,
        )
    return InMemoryEmailProvider()


def construir_enlace_recuperacion(token: str) -> str:
    query = urlencode({"token": token})
    return f"{settings.frontend_url.rstrip('/')}/reset-password?{query}"


def construir_email_recuperacion(
    email: str,
    token: str,
) -> TransactionalEmail:
    enlace = construir_enlace_recuperacion(token)
    enlace_html = escape(enlace, quote=True)
    minutos = settings.password_reset_expire_minutes
    asunto = "Recuperá tu contraseña de Turnelia"
    texto = (
        "Turnelia\n\nRecuperá tu contraseña\n\n"
        "Recibimos una solicitud para cambiar la contraseña de tu cuenta.\n\n"
        f"Restablecer contraseña: {enlace}\n\n"
        f"Este enlace vence en {minutos} minutos.\n\n"
        "Si no solicitaste este cambio, podés ignorar este correo."
    )
    html = f"""<!doctype html>
<html lang="es">
  <body style="margin:0;background:#f6f5f0;color:#1d2927;font-family:Arial,sans-serif">
    <div style="max-width:560px;margin:0 auto;padding:32px 20px">
      <div style="background:#ffffff;border:1px solid #d9e0dc;border-radius:10px;padding:32px">
        <p style="margin:0 0 24px;color:#176f6a;font-size:18px;font-weight:700">Turnelia</p>
        <h1 style="margin:0 0 16px;color:#153e3b;font-size:26px;line-height:1.25">Recuperá tu contraseña</h1>
        <p style="margin:0 0 24px;line-height:1.6">Recibimos una solicitud para cambiar la contraseña de tu cuenta.</p>
        <p style="margin:0 0 24px"><a href="{enlace_html}" style="display:inline-block;padding:12px 18px;border-radius:7px;background:#176f6a;color:#ffffff;text-decoration:none;font-weight:700">Restablecer contraseña</a></p>
        <p style="margin:0 0 12px;color:#65716d;line-height:1.5">Este enlace vence en {minutos} minutos.</p>
        <p style="margin:0 0 20px;color:#65716d;line-height:1.5">Si no solicitaste este cambio, podés ignorar este correo.</p>
        <p style="margin:0;color:#65716d;font-size:12px;line-height:1.5;word-break:break-all">Si el botón no funciona, copiá este enlace:<br>{enlace_html}</p>
      </div>
    </div>
  </body>
</html>"""
    return TransactionalEmail(email, asunto, html, texto)


def enviar_recuperacion_password(email: str, token: str) -> None:
    mensaje = construir_email_recuperacion(email, token)
    try:
        obtener_email_provider().enviar(mensaje)
    except EmailDeliveryError:
        raise
    except Exception as error:
        raise EmailDeliveryError(
            "No se pudo entregar el email transaccional."
        ) from error
