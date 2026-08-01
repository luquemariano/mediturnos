from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.profesional_especialidad import (
    profesionales_especialidades,
)


if TYPE_CHECKING:
    from app.models.profesional import Profesional


class Especialidad(Base):
    __tablename__ = "especialidades"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    nombre: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    descripcion: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    duracion_turno_minutos: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
    )

    activa: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    profesionales: Mapped[list["Profesional"]] = relationship(
        secondary=profesionales_especialidades,
        back_populates="especialidades",
    )