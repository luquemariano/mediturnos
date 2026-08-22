from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from decimal import Decimal


if TYPE_CHECKING:
    from app.models.especialidad import Especialidad
    from app.models.profesional import Profesional


class Prestacion(Base):
    __tablename__ = "prestaciones"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    nombre: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    descripcion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    duracion_minutos: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    precio: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    modalidad: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="presencial",
    )

    activa: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    profesional_id: Mapped[int] = mapped_column(
        ForeignKey("profesionales.id"),
        nullable=False,
    )

    especialidad_id: Mapped[int] = mapped_column(
        ForeignKey("especialidades.id"),
        nullable=False,
    )

    profesional: Mapped["Profesional"] = relationship()
    especialidad: Mapped["Especialidad"] = relationship()
