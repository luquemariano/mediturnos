from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.appointment_reminder import AppointmentReminder


def crear_recordatorio(db: Session, recordatorio: AppointmentReminder) -> AppointmentReminder:
    db.add(recordatorio)
    return recordatorio


def buscar_por_id(db: Session, reminder_id: int) -> AppointmentReminder | None:
    return db.query(AppointmentReminder).filter(AppointmentReminder.id == reminder_id).first()


def listar_por_turno(db: Session, turno_id: int) -> list[AppointmentReminder]:
    return (
        db.query(AppointmentReminder)
        .filter(AppointmentReminder.turno_id == turno_id)
        .order_by(AppointmentReminder.created_at, AppointmentReminder.id)
        .all()
    )


def buscar_ocurrencia(
    db: Session, turno_id: int, channel: str, reminder_type: str,
    appointment_datetime_snapshot: datetime,
) -> AppointmentReminder | None:
    return (
        db.query(AppointmentReminder)
        .filter(
            AppointmentReminder.turno_id == turno_id,
            AppointmentReminder.channel == channel,
            AppointmentReminder.reminder_type == reminder_type,
            AppointmentReminder.appointment_datetime_snapshot == appointment_datetime_snapshot,
        )
        .first()
    )


def listar_candidatos_programados(
    db: Session, ahora: datetime, limite: int | None = None,
) -> list[AppointmentReminder]:
    consulta = (
        db.query(AppointmentReminder)
        .filter(
            AppointmentReminder.status == "pending",
            AppointmentReminder.scheduled_for <= ahora,
        )
        .order_by(AppointmentReminder.scheduled_for, AppointmentReminder.id)
    )
    if limite is not None:
        consulta = consulta.limit(limite)
    return consulta.all()


def reclamar_vencidos(
    db: Session, ahora: datetime, limite: int = 50, confirmar: bool = True,
) -> list[AppointmentReminder]:
    consulta = (
        db.query(AppointmentReminder)
        .filter(
            AppointmentReminder.status == "pending",
            AppointmentReminder.scheduled_for <= ahora,
            or_(
                AppointmentReminder.next_attempt_at.is_(None),
                AppointmentReminder.next_attempt_at <= ahora,
            ),
        )
        .order_by(AppointmentReminder.scheduled_for, AppointmentReminder.id)
        .limit(limite)
    )
    if db.get_bind().dialect.name == "postgresql":
        consulta = consulta.with_for_update(skip_locked=True)
    recordatorios = consulta.all()
    for item in recordatorios:
        item.status = "processing"
        item.processing_started_at = ahora
    db.flush()
    if confirmar:
        db.commit()
    return recordatorios


def recuperar_processing_huerfanos(
    db: Session, limite: datetime, ahora: datetime,
) -> int:
    cantidad = (
        db.query(AppointmentReminder)
        .filter(
            AppointmentReminder.status == "processing",
            AppointmentReminder.processing_started_at.is_not(None),
            AppointmentReminder.processing_started_at < limite,
        )
        .update(
            {
                AppointmentReminder.status: "pending",
                AppointmentReminder.processing_started_at: None,
                AppointmentReminder.next_attempt_at: ahora,
            },
            synchronize_session=False,
        )
    )
    db.commit()
    return cantidad
