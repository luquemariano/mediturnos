from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


if TYPE_CHECKING:
    from app.models.especialidad import Especialidad
    from app.models.profesional import Profesional


class ProfesionalEspecialidad(Base):
    __tablename__ = "profesionales_especialidades"

    profesional_id: Mapped[int] = mapped_column(
        ForeignKey("profesionales.id"),
        primary_key=True,
    )

    especialidad_id: Mapped[int] = mapped_column(
        ForeignKey("especialidades.id"),
        primary_key=True,
    )

    duracion_turno_minutos: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    profesional: Mapped["Profesional"] = relationship(
        back_populates="especialidades_asignadas",
    )

    especialidad: Mapped["Especialidad"] = relationship(
        back_populates="profesionales_asignados",
    )
