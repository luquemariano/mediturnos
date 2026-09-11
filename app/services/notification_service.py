from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.core.datetime_utils import desde_base_utc, utc_a_zona_negocio

def create_public_booking_notification(db: Session, turno, tipo: str, titulo: str, accion: str) -> None:
    user_id = getattr(turno.profesional, "usuario_id", None)
    if user_id is None:
        return
    fecha_hora_local = utc_a_zona_negocio(desde_base_utc(turno.fecha_hora))
    fecha = fecha_hora_local.strftime("%d/%m/%Y")
    hora = fecha_hora_local.strftime("%H:%M")
    paciente = f"{turno.paciente.nombre} {turno.paciente.apellido}".strip()
    mensaje = f"{paciente} {accion} {turno.prestacion.nombre} para el {fecha} a las {hora}."
    db.add(Notification(user_id=user_id, type=tipo, title=titulo, message=mensaje, entity_type="turno", entity_id=turno.id))
    db.commit()


def create_study_results_notification(db: Session, request) -> None:
    user_id = getattr(request.profesional, "usuario_id", None)
    if user_id is None:
        return
    exists = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.type == "study_results_submitted",
        Notification.entity_type == "study_request",
        Notification.entity_id == request.id,
    ).first()
    if exists:
        return
    patient = f"{request.paciente.nombre} {request.paciente.apellido}".strip()
    db.add(Notification(
        user_id=user_id,
        type="study_results_submitted",
        title="Nuevos resultados para revisar",
        message=f"{patient} envió resultados de {request.title}",
        entity_type="study_request",
        entity_id=request.id,
    ))


def list_notifications(db: Session, user_id: int) -> tuple[list[Notification], int]:
    items = db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc(), Notification.id.desc()).limit(30).all()
    unread = db.query(Notification).filter(Notification.user_id == user_id, Notification.read_at.is_(None)).count()
    return items, unread


def mark_notification_read(db: Session, user_id: int, notification_id: int) -> Notification | None:
    item = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()
    if item is None:
        return None
    if item.read_at is None:
        item.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
    return item
