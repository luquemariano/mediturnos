from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


if TYPE_CHECKING:
    from app.models.paciente import Paciente
    from app.models.prestacion import Prestacion


class Turno(Base):
    __tablename__ = "turnos"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    paciente_id: Mapped[int] = mapped_column(
        ForeignKey("pacientes.id"),
        nullable=False,
    )

    prestacion_id: Mapped[int] = mapped_column(
        ForeignKey("prestaciones.id"),
        nullable=False,
    )

    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    estado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="reservado",
    )

    observaciones: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    paciente: Mapped["Paciente"] = relationship()

    prestacion: Mapped["Prestacion"] = relationship()

    @property
    def paciente_nombre(self) -> str:
        return (
            f"{self.paciente.nombre} "
            f"{self.paciente.apellido}"
        )

    @property
    def prestacion_nombre(self) -> str:
        return self.prestacion.nombre

    @property
    def profesional_nombre(self) -> str:
        profesional = self.prestacion.profesional

        return (
            f"{profesional.nombre} "
            f"{profesional.apellido}"
        )

    @property
    def especialidad_nombre(self) -> str:
        return self.prestacion.especialidad.nombre