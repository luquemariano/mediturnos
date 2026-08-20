from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.datetime_utils import ahora_utc
from app.database.connection import Base


class NotificacionMercadoPagoSuscripcion(Base):
    __tablename__ = "notificaciones_mercadopago_suscripcion"
    __table_args__ = (UniqueConstraint("event_key", name="uq_notificaciones_mp_suscripcion_event_key"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_key: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(String(80), nullable=False)
    action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    request_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", server_default="pending")
    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
