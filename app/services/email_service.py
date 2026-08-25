from dataclasses import dataclass
from datetime import datetime
from html import escape
import logging
from typing import Protocol
from urllib.parse import urlencode

import requests

from app.core.datetime_utils import utc_a_zona_negocio


logger = logging.getLogger("mediturnos.email")
development_email_outbox: dict[str, str] = {}
RESEND_API_URL = "https://api.resend.com/emails"
RESEND_TIMEOUT_SECONDS = 10


def __getattr__(nombre: str):
    if nombre == "settings":
        from app.core.config import settings
        return settings
    raise AttributeError(nombre)


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


@dataclass(frozen=True)
class EmailDeliveryResult:
    provider: str
    message_id: str | None = None


class EmailProvider(Protocol):
    def enviar(self, email: TransactionalEmail) -> EmailDeliveryResult: ...


class InMemoryEmailProvider:
    def enviar(self, email: TransactionalEmail) -> EmailDeliveryResult:
        development_email_outbox[email.destinatario] = email.texto
        logger.info("Email transaccional generado en la salida local controlada.")
        return EmailDeliveryResult(provider="in_memory")


class ResendEmailProvider:
    def __init__(self, api_key: str, remitente: str) -> None:
        self._api_key = api_key
        self._remitente = remitente

    def enviar(self, email: TransactionalEmail) -> EmailDeliveryResult:
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
        try:
            message_id = respuesta.json().get("id")
        except (ValueError, AttributeError):
            message_id = None
        return EmailDeliveryResult(provider="resend", message_id=message_id)


def obtener_email_provider(config=None) -> EmailProvider:
    if config is None:
        from app.core.config import settings
        config = settings
    if config.email_provider == "resend":
        if config.resend_api_key is None or not config.email_from:
            raise EmailServiceUnavailable(
                "El proveedor de email no está configurado."
            )
        return ResendEmailProvider(
            config.resend_api_key.get_secret_value(),
            config.email_from,
        )
    return InMemoryEmailProvider()


def construir_enlace_recuperacion(token: str) -> str:
    from app.core.config import settings
    query = urlencode({"token": token})
    return f"{settings.frontend_url.rstrip('/')}/reset-password?{query}"


def construir_email_recuperacion(
    email: str,
    token: str,
) -> TransactionalEmail:
    from app.core.config import settings
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


def _fecha_hora_recordatorio(valor: datetime) -> tuple[str, str]:
    local = utc_a_zona_negocio(valor)
    return local.strftime("%d/%m/%Y"), local.strftime("%H:%M")


def construir_email_recordatorio_turno(
    destinatario: str,
    paciente: str,
    profesional: str,
    especialidad: str,
    prestacion: str | None,
    fecha_hora: datetime,
    zona=None,
    confirm_url: str | None = None,
    cancel_url: str | None = None,
) -> TransactionalEmail:
    local = utc_a_zona_negocio(fecha_hora, zona)
    fecha, hora = local.strftime("%d/%m/%Y"), local.strftime("%H:%M")
    paciente_html = escape(paciente)
    profesional_html = escape(profesional)
    especialidad_html = escape(especialidad)
    prestacion_html = escape(prestacion) if prestacion else None
    fila_prestacion_html = (
        f'<tr><td style="padding:8px 0;color:#65716d">Prestación</td>'
        f'<td style="padding:8px 0;text-align:right;font-weight:700">{prestacion_html}</td></tr>'
        if prestacion_html else ""
    )
    fila_prestacion_texto = f"Prestación: {prestacion}\n" if prestacion else ""
    acciones_texto = ""
    acciones_html = ""
    if confirm_url and cancel_url:
        acciones_texto = f"¿Vas a asistir?\n\nConfirmar turno:\n{confirm_url}\n\nCancelar turno:\n{cancel_url}\n\n"
        acciones_html = f'''<p style="line-height:1.6">¿Vas a asistir? Confirmá o cancelá tu turno:</p>
        <p><a href="{escape(confirm_url, quote=True)}" style="display:inline-block;padding:12px 18px;border-radius:7px;background:#176f6a;color:#fff;text-decoration:none;font-weight:700;margin:4px">Confirmar turno</a></p>
        <p><a href="{escape(cancel_url, quote=True)}" style="display:inline-block;padding:12px 18px;border-radius:7px;background:#65716d;color:#fff;text-decoration:none;font-weight:700;margin:4px">Cancelar turno</a></p>
        <p style="font-size:12px;word-break:break-all">Confirmar: {escape(confirm_url)}<br>Cancelar: {escape(cancel_url)}</p>'''
    asunto = "Recordatorio de tu turno — Turnelia"
    texto = (
        f"Hola, {paciente}.\n\n"
        "Te recordamos que tenés un turno programado.\n\n"
        f"Profesional: {profesional}\n"
        f"Especialidad: {especialidad}\n"
        f"{fila_prestacion_texto}"
        f"Fecha: {fecha}\n"
        f"Hora: {hora}\n\n"
        f"{acciones_texto}"
        "Si necesitás modificar o cancelar tu turno,\n"
        "comunicate con el consultorio.\n\n"
        "Turnelia"
    )
    html = f"""<!doctype html>
<html lang="es"><body style="margin:0;background:#f6f5f0;color:#1d2927;font-family:Arial,sans-serif">
  <div style="max-width:560px;margin:0 auto;padding:24px 16px">
    <div style="background:#fff;border:1px solid #d9e0dc;border-radius:10px;padding:28px">
      <p style="margin:0 0 20px;color:#176f6a;font-size:18px;font-weight:700">Turnelia</p>
      <h1 style="margin:0 0 12px;color:#153e3b;font-size:25px">Recordatorio de turno</h1>
      <p style="line-height:1.6">Hola, {paciente_html}.</p>
      <p style="line-height:1.6">Te recordamos que tenés un turno programado.</p>
      <table style="width:100%;border-collapse:collapse;margin:20px 0">
        <tr><td style="padding:8px 0;color:#65716d">Profesional</td><td style="padding:8px 0;text-align:right;font-weight:700">{profesional_html}</td></tr>
        <tr><td style="padding:8px 0;color:#65716d">Especialidad</td><td style="padding:8px 0;text-align:right;font-weight:700">{especialidad_html}</td></tr>
        {fila_prestacion_html}
        <tr><td style="padding:8px 0;color:#65716d">Fecha</td><td style="padding:8px 0;text-align:right;font-weight:700">{fecha}</td></tr>
        <tr><td style="padding:8px 0;color:#65716d">Hora</td><td style="padding:8px 0;text-align:right;font-weight:700">{hora}</td></tr>
      </table>
      <p style="color:#65716d;line-height:1.6">Si necesitás modificar o cancelar tu turno, comunicate con el consultorio.</p>
      {acciones_html}
      <p style="margin:24px 0 0;color:#65716d">Turnelia</p>
    </div>
  </div>
</body></html>"""
    return TransactionalEmail(destinatario, asunto, html, texto)
