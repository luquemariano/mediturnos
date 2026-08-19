"""Crea datos sintéticos para validar manualmente el flujo real del Cron."""

import argparse
import os
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from pydantic import TypeAdapter
from pydantic.networks import EmailStr
from sqlalchemy.orm import Session

from app.core.datetime_utils import a_utc
from app.database.connection import SessionLocal
from app.models.appointment_reminder import AppointmentReminder
from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.turno import Turno
from app.schemas.turno import TurnoCrear
from app.services.turno_service import crear_turno

MARCADOR = "TEST CONTROLADO CONFIRM/CANCEL"
EMAIL = TypeAdapter(EmailStr)


def _require_environment() -> str:
    if os.getenv("CONTROLLED_PRODUCTION_TEST") != "true":
        raise SystemExit("Abortado: requiere CONTROLLED_PRODUCTION_TEST=true")
    if os.getenv("APP_ENV") != "production":
        raise SystemExit("Abortado: requiere APP_ENV=production")
    recipient = os.getenv("CONTROLLED_TEST_EMAIL", "").strip()
    if not recipient:
        raise SystemExit("Abortado: falta CONTROLLED_TEST_EMAIL")
    try:
        return str(EMAIL.validate_python(recipient)).lower()
    except Exception as error:
        raise SystemExit("Abortado: CONTROLLED_TEST_EMAIL no es válido") from error


def _existing(db: Session, recipient: str):
    return (
        db.query(Turno)
        .join(Paciente, Turno.paciente_id == Paciente.id)
        .filter(Paciente.email == recipient, Paciente.nombre == "Turnelia", Paciente.apellido == "Prueba Confirmacion", Turno.observaciones == MARCADOR)
        .order_by(Turno.id.desc())
        .first()
    )


def _print_existing(db: Session, turno: Turno) -> None:
    reminder = db.query(AppointmentReminder).filter(AppointmentReminder.turno_id == turno.id).order_by(AppointmentReminder.id.desc()).first()
    local = turno.fecha_hora.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
    print("Controlled test already exists")
    print(f"Patient ID: {turno.paciente_id}")
    print(f"Appointment ID: {turno.id}")
    print(f"Appointment datetime: {local:%d/%m/%Y %H:%M}")
    print(f"Appointment status: {turno.estado}")
    print(f"Reminder status: {reminder.status if reminder else 'not_created'}")
    print(f"Reminder sent: {'yes' if reminder and reminder.sent_at else 'no'}")


def _find_slot(db: Session, prestacion: Prestacion) -> datetime:
    now = datetime.now(UTC)
    local_now = now.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
    candidate = local_now.replace(second=0, microsecond=0) + timedelta(hours=2)
    for _ in range(48):
        try:
            candidate_utc = a_utc(candidate)
            if candidate_utc <= now + timedelta(hours=12):
                return candidate_utc
            candidate += timedelta(minutes=15)
        except Exception:
            candidate += timedelta(minutes=15)
    raise RuntimeError("No se encontró un horario futuro controlable.")


def create_controlled_test(db: Session, recipient: str):
    existing = _existing(db, recipient)
    if existing:
        _print_existing(db, existing)
        return existing
    prestacion = (
        db.query(Prestacion)
        .join(Profesional, Prestacion.profesional_id == Profesional.id)
        .filter(Prestacion.activa.is_(True), Profesional.activo.is_(True))
        .order_by(Prestacion.id)
        .first()
    )
    if prestacion is None:
        raise RuntimeError("No existe un profesional activo con prestación activa.")
    paciente = Paciente(nombre="Turnelia", apellido="Prueba Confirmacion", email=recipient, dni=None, telefono=None, activo=True)
    db.add(paciente)
    db.flush()
    turno = crear_turno(db, TurnoCrear(paciente_id=paciente.id, prestacion_id=prestacion.id, fecha_hora=_find_slot(db, prestacion), observaciones=MARCADOR))
    print("CONTROLLED APPOINTMENT TEST CREATED")
    print("Environment: production")
    print("Database: configured")
    print("Recipient configured: yes")
    print(f"Professional ID: {prestacion.profesional_id}")
    print(f"Professional display name: {prestacion.profesional.nombre} {prestacion.profesional.apellido}")
    local = turno.fecha_hora.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
    print(f"Patient ID: {paciente.id}")
    print(f"Appointment ID: {turno.id}")
    print(f"Status: {turno.estado}")
    print(f"Appointment: {local:%d/%m/%Y %H:%M}")
    print("Reminder existing: no")
    print("Eligible for reminder: yes")
    print("Next step:")
    print("Wait for the next Render reminder cron run.")
    return turno


def status(db: Session, recipient: str) -> None:
    turno = _existing(db, recipient)
    if not turno:
        raise SystemExit("Controlled test not found")
    _print_existing(db, turno)


def main() -> int:
    recipient = _require_environment()
    print("CONTROLLED APPOINTMENT TEST")
    print("Environment: production")
    print("Database: configured")
    print("Recipient: configured")
    db = SessionLocal()
    try:
        if os.getenv("_CONTROLLED_STATUS") == "true":
            status(db, recipient)
        else:
            create_controlled_test(db, recipient)
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    os.environ["_CONTROLLED_STATUS"] = "true" if args.status else "false"
    raise SystemExit(main())
