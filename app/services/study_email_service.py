from datetime import datetime
from html import escape
import logging

from app.core.config import settings
from app.services.email_service import EmailDeliveryError, TransactionalEmail, obtener_email_provider
from app.services.study_access_token_service import create_study_access_token

logger = logging.getLogger("mediturnos.study_email")

DISPOSITION_MESSAGES = {
    "online_response": "Tu profesional revisó los resultados. Para conocer la devolución, comunicate con el consultorio.",
    "requires_in_person": "Tu profesional recomienda una consulta presencial.",
    "requires_teleconsultation": "Tu profesional recomienda una teleconsulta.",
}


def _send(message: TransactionalEmail) -> bool:
    try:
        obtener_email_provider().enviar(message)
        return True
    except (EmailDeliveryError, Exception):
        logger.warning("No se pudo entregar una notificación de estudio.")
        return False


def _layout(title: str, body: str, cta: str | None = None, url: str | None = None) -> tuple[str, str]:
    safe_url = escape(url, quote=True) if url else None
    button = f'<p><a href="{safe_url}" style="display:inline-block;padding:12px 18px;border-radius:7px;background:#176f6a;color:#fff;text-decoration:none;font-weight:700">{escape(cta or "Ver información")}</a></p>' if safe_url else ""
    fallback = f"\n\n{url}" if url else ""
    text = f"Turnelia\n\n{title}\n\n{body}{fallback}\n\nSi no reconocés esta notificación, podés ignorar este mensaje.\n\nTurnelia"
    html = f'<!doctype html><html lang="es"><body style="margin:0;background:#f6f5f0;color:#1d2927;font-family:Arial,sans-serif"><div style="max-width:560px;margin:0 auto;padding:24px 16px"><div style="background:#fff;border:1px solid #d9e0dc;border-radius:10px;padding:28px"><p style="color:#176f6a;font-size:18px;font-weight:700">Turnelia</p><h1 style="color:#153e3b;font-size:25px">{escape(title)}</h1><p style="line-height:1.6">{escape(body).replace(chr(10), "<br>")}</p>{button}<p style="color:#65716d;font-size:12px;line-height:1.5">Si no reconocés esta notificación, podés ignorar este mensaje.</p></div></div></body></html>'
    return html, text


def _patient_email(patient) -> str | None:
    value = (getattr(patient, "email", None) or "").strip()
    return value or None


def _professional_email(professional) -> str | None:
    value = (getattr(professional, "email", None) or "").strip()
    if not value and getattr(professional, "usuario", None):
        value = (getattr(professional.usuario, "email", None) or "").strip()
    return value or None


def notify_new_request(request) -> bool:
    recipient = _patient_email(request.paciente)
    if not recipient or not settings.study_access_secret:
        return False
    token = create_study_access_token(secret=settings.study_access_secret.get_secret_value(), study_request_id=request.id, patient_id=request.paciente_id)
    url = f"{settings.frontend_url.rstrip('/')}/estudios/enviar?token={token}"
    professional = f"{request.profesional.nombre} {request.profesional.apellido}".strip()
    expiration = f" El enlace vence el {request.expires_at.isoformat()}." if request.expires_at else ""
    body = f"Hola, {request.paciente.nombre}.\n\n{professional} te envió una nueva solicitud de estudio: {request.title}.\n\n{request.instructions or 'No se agregaron instrucciones adicionales.'}{expiration}\n\nEste enlace es personal y seguro."
    html, text = _layout("Tenés una nueva solicitud de estudio", body, "Enviar resultados", url)
    return _send(TransactionalEmail(recipient, "Turnelia — Tenés una nueva solicitud de estudio", html, text))


def notify_results_submitted(request, documents_count: int, submitted_at: datetime) -> bool:
    recipient = _professional_email(request.profesional)
    if not recipient:
        return False
    body = f"Se recibieron {documents_count} archivo(s) de {request.paciente.nombre} {request.paciente.apellido}.\n\nEstudio: {request.title}.\nFecha: {submitted_at.isoformat()}."
    url = f"{settings.frontend_url.rstrip('/')}/dashboard"
    html, text = _layout("Nuevos resultados para revisar", body, "Ver estudios pendientes", url)
    return _send(TransactionalEmail(recipient, "Turnelia — Nuevos resultados para revisar", html, text))


def notify_review_created(review) -> bool:
    recipient = _patient_email(review.study_request.paciente)
    if not recipient:
        return False
    disposition = DISPOSITION_MESSAGES.get(review.disposition, "Tu profesional revisó los resultados. Comunicate con el consultorio.")
    body = f"Hola, {review.study_request.paciente.nombre}.\n\nTu profesional revisó los resultados del estudio {review.study_request.title}.\n\n{disposition}"
    html, text = _layout("Tu profesional revisó los resultados", body)
    return _send(TransactionalEmail(recipient, "Turnelia — Tus resultados fueron revisados", html, text))
