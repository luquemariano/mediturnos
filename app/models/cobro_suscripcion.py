from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import ahora_utc
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.suscripcion import Suscripcion


class CobroSuscripcion(Base):
    __tablename__ = "cobros_suscripcion"
    __table_args__ = (
        UniqueConstraint("mp_authorized_payment_id", name="uq_cobros_suscripcion_authorized_payment"),
        UniqueConstraint("mp_payment_id", name="uq_cobros_suscripcion_payment"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    suscripcion_id: Mapped[int] = mapped_column(ForeignKey("suscripciones.id", ondelete="CASCADE"), nullable=False, index=True)
    mp_authorized_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mp_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    status_detail: Mapped[str | None] = mapped_column(String(100), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc, onupdate=ahora_utc)

    suscripcion: Mapped["Suscripcion"] = relationship(back_populates="cobros")
