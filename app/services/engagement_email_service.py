"""Optional Turnelia news and quality follow-up email rendering and delivery."""

from dataclasses import dataclass
from html import escape
from urllib.parse import urlsplit

from app.services.email_service import (
    EmailDeliveryResult,
    TransactionalEmail,
    obtener_email_provider,
)


@dataclass(frozen=True)
class EngagementEmail:
    destinatario: str
    nombre: str
    titulo: str
    preheader: str
    mensaje_principal: str
    novedades: tuple[str, ...] = ()
    cta: str | None = None
    url_cta: str | None = None
    enlace_gestion_baja: str | None = None


class EngagementEmailURLInvalida(ValueError):
    """Raised when an optional email link is not an absolute HTTP(S) URL."""


def _validar_url_segura(valor: str | None, campo: str) -> str | None:
    if valor is None:
        return None
    try:
        partes = urlsplit(valor)
        host = partes.hostname
        puerto = partes.port
    except (TypeError, ValueError) as error:
        raise EngagementEmailURLInvalida(
            f"{campo} debe ser una URL absoluta HTTP o HTTPS válida."
        ) from error
    if (
        partes.scheme.lower() not in {"http", "https"}
        or not partes.netloc
        or not host
        or partes.username is not None
        or partes.password is not None
        or partes.netloc.endswith(":")
        or any(
            caracter.isspace()
            or ord(caracter) < 32
            or 127 <= ord(caracter) <= 159
            or caracter == "\\"
            for caracter in valor
        )
        or (puerto is not None and not 1 <= puerto <= 65535)
    ):
        raise EngagementEmailURLInvalida(
            f"{campo} debe ser una URL absoluta HTTP o HTTPS válida."
        )
    return valor


def construir_email_engagement(datos: EngagementEmail) -> TransactionalEmail:
    """Render an optional, explicitly requested quality/news message."""

    url_cta = _validar_url_segura(datos.url_cta, "La URL del botón")
    enlace_gestion_baja = _validar_url_segura(
        datos.enlace_gestion_baja, "El enlace de gestión o baja"
    )

    def safe(value: str) -> str:
        return escape(value, quote=True)

    novedades = "".join(f"<li style=\"margin:0 0 10px;line-height:1.6\">{safe(item)}</li>" for item in datos.novedades)
    bloque_novedades = (
        f'<ul style="padding-left:22px;margin:16px 0">{novedades}</ul>'
        if novedades else ""
    )
    boton = ""
    lineas_cta = ""
    if datos.cta and url_cta:
        boton = (f'<p style="margin:24px 0"><a href="{safe(url_cta)}" '
                 f'style="display:inline-block;padding:12px 18px;border-radius:7px;background:#176f6a;color:#fff;text-decoration:none;font-weight:700">{safe(datos.cta)}</a></p>')
        lineas_cta = f"\n\n{datos.cta}: {url_cta}"
    gestion_html = ""
    gestion_texto = ""
    if enlace_gestion_baja:
        gestion_html = (f'<p style="margin:24px 0 0;color:#65716d;font-size:12px;line-height:1.6">'
                        f'Podés gestionar esta preferencia o darte de baja desde '
                        f'<a href="{safe(enlace_gestion_baja)}" style="color:#176f6a">este enlace</a>.</p>')
        gestion_texto = f"\n\nGestionar preferencias o darte de baja: {enlace_gestion_baja}"
    texto_novedades = "\n".join(f"• {item}" for item in datos.novedades)
    asunto = f"{datos.titulo} — Turnelia"
    bloque_texto_novedades = f"\n\n{texto_novedades}" if texto_novedades else ""
    texto = (f"Turnelia\n\n{datos.titulo}\n\nHola, {datos.nombre}.\n\n"
             f"{datos.mensaje_principal}{bloque_texto_novedades}"
             f"{lineas_cta}{gestion_texto}\n\nTurnelia")
    html = f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="x-apple-disable-message-reformatting"><title>{safe(datos.titulo)}</title></head>
<body style="margin:0;background:#f6f5f0;color:#1d2927;font-family:Arial,sans-serif">
  <span style="display:none!important;visibility:hidden;opacity:0;color:transparent;height:0;width:0;overflow:hidden">{safe(datos.preheader)}</span>
  <div style="width:100%;background:#f6f5f0"><div style="max-width:560px;margin:0 auto;padding:28px 16px">
    <div style="background:#fff;border:1px solid #d9e0dc;border-radius:10px;padding:28px">
      <p style="margin:0 0 20px;color:#176f6a;font-size:18px;font-weight:700">Turnelia</p>
      <h1 style="margin:0 0 16px;color:#153e3b;font-size:25px;line-height:1.3">{safe(datos.titulo)}</h1>
      <p style="margin:0 0 12px;line-height:1.6">Hola, {safe(datos.nombre)}.</p>
      <p style="margin:0;line-height:1.6;white-space:pre-line">{safe(datos.mensaje_principal)}</p>
      {bloque_novedades}{boton}{gestion_html}
    </div>
  </div></div>
</body></html>'''
    return TransactionalEmail(datos.destinatario, asunto, html, texto)


def enviar_email_engagement(datos: EngagementEmail) -> EmailDeliveryResult:
    """Deliver only when a caller explicitly invokes this function."""
    return obtener_email_provider().enviar(construir_email_engagement(datos))
