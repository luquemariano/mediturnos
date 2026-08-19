import html
import logging
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import obtener_db
from app.services.appointment_action_service import AppointmentActionError, apply_appointment_action
from app.services.appointment_action_token_service import AppointmentActionTokenError, verify_appointment_action_token

logger = logging.getLogger("mediturnos.appointment_action")
router = APIRouter(prefix="/turnos/public", tags=["Acciones públicas de turnos"])


def _page(title: str, message: str, turno=None) -> HTMLResponse:
    details = ""
    if turno is not None:
        local = turno.fecha_hora.astimezone(ZoneInfo(settings.app_timezone))
        professional = html.escape(turno.profesional_nombre)
        details = f"<p>{local:%d/%m/%Y} · {local:%H:%M}</p><p>{professional}</p>"
    return HTMLResponse(f"<!doctype html><html lang='es'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Turnelia</title><body style='font-family:Arial;max-width:560px;margin:4rem auto;padding:1rem;color:#153e3b'><h1>Turnelia</h1><h2>{html.escape(title)}</h2><p>{html.escape(message)}</p>{details}<p>Ya podés cerrar esta ventana.</p></body></html>")


def _action(token: str, action: str, db: Session):
    try:
        turno, result = apply_appointment_action(db, token=token, secret=settings.appointment_action_secret.get_secret_value(), action=action, now=datetime.now(UTC))
    except AppointmentActionError as error:
        messages = {"invalid_token": "Este enlace no es válido.", "invalid_scope": "Este enlace no corresponde a esta acción.", "expired": "Este enlace ya expiró.", "rescheduled": "Este enlace ya no es válido porque el turno fue reprogramado.", "passed": "Este enlace ya no es válido porque el turno ya pasó.", "not_found": "No encontramos el turno asociado.", "not_allowed": "Esta acción no está disponible para el estado actual del turno."}
        return _page("Enlace no válido", messages.get(error.args[0], "No se pudo procesar la acción."))
    if action == "confirm":
        return _page("Turno confirmado", "Tu turno fue confirmado correctamente." if result == "confirm" else "Este turno ya estaba confirmado.", turno)
    return _page("Turno cancelado", "Tu turno fue cancelado correctamente." if result == "cancel" else "Este turno ya estaba cancelado.", turno)


def _preview(token: str, action: str) -> HTMLResponse:
    try:
        verify_appointment_action_token(token=token, secret=settings.appointment_action_secret.get_secret_value(), expected_scope=action)
    except AppointmentActionTokenError:
        return _page("Enlace no válido", "Este enlace no es válido o ya expiró.")
    label = "confirmar" if action == "confirm" else "cancelar"
    safe_token = html.escape(token, quote=True)
    return HTMLResponse(f"<!doctype html><html lang='es'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Turnelia</title><body style='font-family:Arial;max-width:560px;margin:4rem auto;padding:1rem;color:#153e3b'><h1>Turnelia</h1><h2>¿Querés {label} este turno?</h2><p>Presioná el botón para confirmar la acción.</p><form method='post' action='?token={safe_token}'><button type='submit' style='padding:12px 18px;border:0;border-radius:7px;background:#176f6a;color:white;font-weight:700'>{label.title()} turno</button></form></body></html>")


@router.get("/confirmar", response_class=HTMLResponse)
def confirmar_turno_publico(token: str = Query(...), db: Session = Depends(obtener_db)):
    return _preview(token, "confirm")


@router.post("/confirmar", response_class=HTMLResponse)
def confirmar_turno_publico_post(token: str = Query(...), db: Session = Depends(obtener_db)):
    return _action(token, "confirm", db)


@router.get("/cancelar", response_class=HTMLResponse)
def cancelar_turno_publico(token: str = Query(...), db: Session = Depends(obtener_db)):
    return _preview(token, "cancel")


@router.post("/cancelar", response_class=HTMLResponse)
def cancelar_turno_publico_post(token: str = Query(...), db: Session = Depends(obtener_db)):
    return _action(token, "cancel", db)
