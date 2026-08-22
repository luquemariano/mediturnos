from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


if TYPE_CHECKING:
    from app.models.profesional import Profesional


class Disponibilidad(Base):
    __tablename__ = "disponibilidades"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    profesional_id: Mapped[int] = mapped_column(
        ForeignKey("profesionales.id"),
        nullable=False,
        index=True,
    )

    dia_semana: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    hora_inicio: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    hora_fin: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    activa: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    profesional: Mapped["Profesional"] = relationship()
