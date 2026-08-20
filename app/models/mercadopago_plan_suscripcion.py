from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.datetime_utils import ahora_utc
from app.database.connection import Base


class MercadoPagoPlanSuscripcion(Base):
    __tablename__ = "mercadopago_planes_suscripcion"
    __table_args__ = (
        CheckConstraint("plan_code IN ('profesional', 'consultorio', 'centro')", name="ck_mp_planes_suscripcion_plan"),
        CheckConstraint("environment IN ('sandbox', 'production')", name="ck_mp_planes_suscripcion_environment"),
        UniqueConstraint("plan_code", "environment", name="uq_mp_planes_suscripcion_plan_environment"),
        UniqueConstraint("mp_preapproval_plan_id", name="uq_mp_planes_suscripcion_external_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plan_code: Mapped[str] = mapped_column(String(30), nullable=False)
    environment: Mapped[str] = mapped_column(String(20), nullable=False)
    mp_preapproval_plan_id: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="ARS", server_default="ARS")
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc, onupdate=ahora_utc)
