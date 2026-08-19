from datetime import UTC, datetime, timedelta

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.datetime_utils import ahora_utc
from app.models.appointment_reminder import AppointmentReminder
from app.models.prestacion import Prestacion
from app.models.turno import Turno
from app.repositories.appointment_reminder_repository import (
    buscar_ocurrencia,
    crear_recordatorio,
    reclamar_vencidos,
    recuperar_processing_huerfanos,
)
from app.services.email_service import (
    EmailDeliveryError,
    construir_email_recordatorio_turno,
    obtener_email_provider,
)

ESTADOS_NOTIFICABLES = {"reservado", "confirmado"}
MAX_INTENTOS = 3
PROCESSING_TIMEOUT = timedelta(minutes=20)
BACKOFFS = (timedelta(minutes=5), timedelta(minutes=30))
EMAIL_ADAPTER = TypeAdapter(EmailStr)


def _utc(valor: datetime) -> datetime:
    if valor.tzinfo is None:
        return valor.replace(tzinfo=UTC)
    return valor.astimezone(UTC)


def _email_normalizado(email: str | None) -> tuple[str | None, str | None]:
    valor = (email or "").strip()
    if not valor:
        return None, "missing_email"
    try:
        return str(EMAIL_ADAPTER.validate_python(valor)).lower(), None
    except ValidationError:
        return None, "invalid_email"


def _turnos_candidatos(db: Session, ahora: datetime, ventana: timedelta) -> list[Turno]:
    # La fecha de ejecución es el límite inferior: cualquier recordatorio
    # cuyo scheduled_for ya venció debe poder generarse tras un downtime.
    hasta = ahora + timedelta(hours=24)
    return (
        db.query(Turno)
        .options(
            joinedload(Turno.paciente),
            joinedload(Turno.profesional),
            joinedload(Turno.prestacion).joinedload(Prestacion.especialidad),
        )
        .filter(
            Turno.estado.in_(ESTADOS_NOTIFICABLES),
            Turno.fecha_hora > ahora,
            Turno.fecha_hora <= hasta,
        )
        .all()
    )


def generate_upcoming_reminders(
    db: Session, ahora: datetime | None = None, ventana: timedelta = timedelta(minutes=15),
) -> list[AppointmentReminder]:
    ahora = _utc(ahora or ahora_utc())
    creados: list[AppointmentReminder] = []
    for turno in _turnos_candidatos(db, ahora, ventana):
        snapshot = _utc(turno.fecha_hora)
        if buscar_ocurrencia(db, turno.id, "email", "24h", snapshot):
            continue
        email, motivo = _email_normalizado(turno.paciente.email if turno.paciente else None)
        item = AppointmentReminder(
            turno_id=turno.id,
            channel="email",
            reminder_type="24h",
            status="skipped" if motivo else "pending",
            appointment_datetime_snapshot=snapshot,
            recipient_email_snapshot=email or "",
            patient_name_snapshot=f"{turno.paciente.nombre} {turno.paciente.apellido}",
            professional_name_snapshot=f"{turno.profesional.nombre} {turno.profesional.apellido}",
            specialty_name_snapshot=turno.prestacion.especialidad.nombre,
            service_name_snapshot=turno.prestacion.nombre,
            scheduled_for=snapshot - timedelta(hours=24),
            skip_reason=motivo,
        )
        try:
            with db.begin_nested():
                crear_recordatorio(db, item)
                db.flush()
        except IntegrityError:
            continue
        creados.append(item)
    db.commit()
    return creados


def validate_reminder(db: Session, reminder: AppointmentReminder, ahora: datetime | None = None) -> str | None:
    ahora = _utc(ahora or ahora_utc())
    turno = db.get(Turno, reminder.turno_id)
    if turno is None or turno.estado not in ESTADOS_NOTIFICABLES:
        return "cancelled" if turno and turno.estado == "cancelado" else "appointment_unavailable"
    if _utc(turno.fecha_hora) != _utc(reminder.appointment_datetime_snapshot):
        return "rescheduled"
    if _utc(turno.fecha_hora) <= ahora:
        return "appointment_passed"
    return None


def process_claimed_reminder(db: Session, reminder: AppointmentReminder, ahora: datetime | None = None) -> str:
    motivo = validate_reminder(db, reminder, ahora)
    if motivo:
        reminder.status = "skipped"
        reminder.skip_reason = motivo
        db.commit()
        return "skipped"
    return reminder.status


def claim_due_reminders(db: Session, ahora: datetime | None = None, limite: int = 50) -> list[AppointmentReminder]:
    ahora = _utc(ahora or ahora_utc())
    return reclamar_vencidos(db, ahora, limite)


def recover_stale_processing(db: Session, ahora: datetime | None = None) -> int:
    ahora = _utc(ahora or ahora_utc())
    return recuperar_processing_huerfanos(db, ahora - PROCESSING_TIMEOUT, ahora)


def schedule_retry(db: Session, reminder: AppointmentReminder, error: str, ahora: datetime | None = None) -> str:
    ahora = _utc(ahora or ahora_utc())
    reminder.attempt_count += 1
    reminder.last_error = error[:1000]
    reminder.processing_started_at = None
    if reminder.attempt_count >= MAX_INTENTOS:
        reminder.status = "failed"
        reminder.next_attempt_at = None
        resultado = "failed"
    else:
        reminder.status = "pending"
        reminder.next_attempt_at = ahora + BACKOFFS[reminder.attempt_count - 1]
        resultado = "pending"
    db.commit()
    return resultado


def mark_failed(db: Session, reminder: AppointmentReminder, error: str) -> None:
    reminder.status = "failed"
    reminder.last_error = error[:1000]
    reminder.processing_started_at = None
    db.commit()


def send_claimed_reminder(
    db: Session,
    reminder: AppointmentReminder,
    ahora: datetime | None = None,
) -> str:
    ahora = _utc(ahora or ahora_utc())
    motivo = validate_reminder(db, reminder, ahora)
    if motivo:
        reminder.status = "skipped"
        reminder.skip_reason = motivo
        db.commit()
        return "skipped"
    mensaje = construir_email_recordatorio_turno(
        destinatario=reminder.recipient_email_snapshot,
        paciente=reminder.patient_name_snapshot,
        profesional=reminder.professional_name_snapshot,
        especialidad=reminder.specialty_name_snapshot,
        prestacion=reminder.service_name_snapshot,
        fecha_hora=_utc(reminder.appointment_datetime_snapshot),
    )
    try:
        resultado = obtener_email_provider().enviar(mensaje)
    except EmailDeliveryError as error:
        return schedule_retry(db, reminder, str(error), ahora)
    except Exception:
        return schedule_retry(db, reminder, "email_provider_error", ahora)
    reminder.status = "sent"
    reminder.sent_at = ahora
    reminder.provider = resultado.provider
    reminder.provider_message_id = resultado.message_id
    reminder.processing_started_at = None
    db.commit()
    return "sent"
