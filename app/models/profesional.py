from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base
from app.models.profesional_especialidad import (
    profesionales_especialidades,
)


if TYPE_CHECKING:
    from app.models.especialidad import Especialidad


class Profesional(Base):
    __tablename__ = "profesionales"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    apellido: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    matricula: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    telefono: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    especialidades: Mapped[list["Especialidad"]] = relationship(
        secondary=profesionales_especialidades,
        back_populates="profesionales",
    )