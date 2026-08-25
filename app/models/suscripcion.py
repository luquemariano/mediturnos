from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import ahora_utc
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.cuenta import Cuenta
    from app.models.cobro_suscripcion import CobroSuscripcion


class Suscripcion(Base):
    __tablename__ = "suscripciones"
    __table_args__ = (
        CheckConstraint("plan_code IN ('profesional', 'consultorio', 'centro')", name="ck_suscripciones_plan"),
        CheckConstraint("status IN ('trial', 'active', 'past_due', 'cancelled', 'expired')", name="ck_suscripciones_status"),
        CheckConstraint("billing_provider IN ('manual', 'mercadopago')", name="ck_suscripciones_billing_provider"),
        UniqueConstraint("cuenta_id", name="uq_suscripciones_cuenta_id"),
        UniqueConstraint("external_reference", name="uq_suscripciones_external_reference"),
        UniqueConstraint("mp_preapproval_id", name="uq_suscripciones_mp_preapproval_id"),
        UniqueConstraint("mp_idempotency_key", name="uq_suscripciones_mp_idempotency_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cuenta_id: Mapped[int] = mapped_column(ForeignKey("cuentas.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    plan_code: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    trial_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    billing_provider: Mapped[str] = mapped_column(String(30), nullable=False, default="manual", server_default="manual")
    external_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mp_preapproval_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mp_idempotency_key: Mapped[str | None] = mapped_column(String(36), nullable=True)
    mp_preapproval_plan_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mp_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mp_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    billing_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    billing_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    next_payment_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    billing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mp_last_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mp_last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc, onupdate=ahora_utc)

    cuenta: Mapped["Cuenta"] = relationship(back_populates="suscripcion")
    cobros: Mapped[list["CobroSuscripcion"]] = relationship(back_populates="suscripcion", cascade="all, delete-orphan")
