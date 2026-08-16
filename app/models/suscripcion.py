from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import ahora_utc
from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.cuenta import Cuenta


class Suscripcion(Base):
    __tablename__ = "suscripciones"
    __table_args__ = (
        CheckConstraint("plan_code IN ('profesional', 'consultorio', 'centro')", name="ck_suscripciones_plan"),
        CheckConstraint("status IN ('trial', 'active', 'past_due', 'cancelled', 'expired')", name="ck_suscripciones_status"),
        UniqueConstraint("cuenta_id", name="uq_suscripciones_cuenta_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cuenta_id: Mapped[int] = mapped_column(ForeignKey("cuentas.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    plan_code: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    trial_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc, onupdate=ahora_utc)

    cuenta: Mapped["Cuenta"] = relationship(back_populates="suscripcion")
