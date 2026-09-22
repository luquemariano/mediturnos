from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.datetime_utils import ahora_utc
from app.models.message_delivery import MessageDelivery
from app.repositories.message_delivery_repository import (
    buscar_por_idempotency_key,
    crear_delivery,
    reclamar_pendientes,
    recuperar_processing_huerfanos,
)


def _required(value: str, name: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValueError(f"{name} no puede estar vacío")
    return value


def _sanitize_error(error: str) -> str:
    value = " ".join(str(error).split())
    for marker in ("Authorization:", "access_token=", "verify_token=", "token="):
        if marker.lower() in value.lower():
            return "messaging_provider_error"
    return value[:1000]


def _is_idempotency_violation(error: IntegrityError) -> bool:
    detail = str(getattr(error, "orig", error)).lower()
    return "uq_message_deliveries_idempotency_key" in detail or "idempotency_key" in detail


def create_delivery(
    db: Session,
    *,
    channel: str,
    purpose: str,
    recipient_snapshot: str,
    idempotency_key: str,
    message_type: str,
) -> MessageDelivery:
    values = {
        "channel": channel,
        "purpose": purpose,
        "recipient_snapshot": recipient_snapshot,
        "idempotency_key": idempotency_key,
        "message_type": message_type,
    }
    for name, value in values.items():
        values[name] = _required(value, name)
    existing = buscar_por_idempotency_key(db, values["idempotency_key"])
    if existing:
        return existing
    delivery = MessageDelivery(**values)
    try:
        with db.begin_nested():
            crear_delivery(db, delivery)
            db.flush()
    except IntegrityError as error:
        if not _is_idempotency_violation(error):
            raise
        existing = buscar_por_idempotency_key(db, values["idempotency_key"])
        if existing:
            return existing
        raise
    return delivery


def get_delivery_by_idempotency_key(db: Session, key: str) -> MessageDelivery | None:
    return buscar_por_idempotency_key(db, key)


def claim_pending(db: Session, ahora: datetime | None = None, limite: int = 50) -> list[MessageDelivery]:
    return reclamar_pendientes(db, ahora or ahora_utc(), limite)


def recover_stale_processing(
    db: Session,
    ahora: datetime | None = None,
    timeout: timedelta = timedelta(minutes=20),
) -> int:
    ahora = ahora or ahora_utc()
    return recuperar_processing_huerfanos(db, ahora - timeout, ahora)


def mark_sent(db: Session, delivery: MessageDelivery, *, provider: str, provider_message_id: str | None = None, ahora: datetime | None = None) -> MessageDelivery:
    delivery.status = "sent"
    delivery.provider = _required(provider, "provider")
    delivery.provider_message_id = provider_message_id
    delivery.sent_at = ahora or ahora_utc()
    delivery.processing_started_at = None
    delivery.last_error = None
    db.flush()
    return delivery


def mark_failed(db: Session, delivery: MessageDelivery, error: str) -> MessageDelivery:
    delivery.status = "failed"
    delivery.last_error = _sanitize_error(error)
    delivery.processing_started_at = None
    db.flush()
    return delivery
