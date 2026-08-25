from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


if TYPE_CHECKING:
    from app.models.turno import Turno


class Pago(Base):
    __tablename__ = "pagos"
    __table_args__ = (
        UniqueConstraint(
            "turno_id",
            name="uq_pagos_turno_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    turno_id: Mapped[int] = mapped_column(
        ForeignKey("turnos.id"),
        nullable=False,
        index=True,
    )

    preference_id: Mapped[str | None] = mapped_column(
        String(150),
        unique=True,
        nullable=True,
    )

    payment_id: Mapped[str | None] = mapped_column(
        String(150),
        unique=True,
        nullable=True,
    )

    estado: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pendiente",
    )

    monto: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    init_point: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    requiere_revision: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    motivo_revision: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    mp_actualizado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    creado_en: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )

    turno: Mapped["Turno"] = relationship()
