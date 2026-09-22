from datetime import datetime

from sqlalchemy.orm import Session

from app.models.message_delivery import MessageDelivery


def crear_delivery(db: Session, delivery: MessageDelivery) -> MessageDelivery:
    db.add(delivery)
    return delivery


def buscar_por_idempotency_key(db: Session, key: str) -> MessageDelivery | None:
    return db.query(MessageDelivery).filter(MessageDelivery.idempotency_key == key).first()


def reclamar_pendientes(db: Session, ahora: datetime, limite: int = 50) -> list[MessageDelivery]:
    consulta = (
        db.query(MessageDelivery)
        .filter(
            MessageDelivery.status == "pending",
            (MessageDelivery.next_attempt_at.is_(None)) | (MessageDelivery.next_attempt_at <= ahora),
        )
        .order_by(MessageDelivery.created_at, MessageDelivery.id)
        .limit(limite)
    )
    if db.get_bind().dialect.name == "postgresql":
        consulta = consulta.with_for_update(skip_locked=True)
    deliveries = consulta.all()
    for delivery in deliveries:
        delivery.status = "processing"
        delivery.attempt_count += 1
        delivery.processing_started_at = ahora
    db.flush()
    return deliveries


def recuperar_processing_huerfanos(db: Session, limite: datetime, ahora: datetime) -> int:
    cantidad = (
        db.query(MessageDelivery)
        .filter(
            MessageDelivery.status == "processing",
            MessageDelivery.processing_started_at.is_not(None),
            MessageDelivery.processing_started_at < limite,
        )
        .update(
            {
                MessageDelivery.status: "pending",
                MessageDelivery.processing_started_at: None,
                MessageDelivery.next_attempt_at: ahora,
            },
            synchronize_session=False,
        )
    )
    db.flush()
    return cantidad
