from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.especialidad import Especialidad


class ActividadProfesional(Base):
    """Configuración confiable de los requisitos para cada actividad."""

    __tablename__ = "actividades_profesionales"
    __table_args__ = (
        CheckConstraint(
            "requiere_especialidad OR especialidad_predeterminada_id IS NOT NULL",
            name="ck_actividad_profesional_especialidad_resuelta",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    requiere_matricula: Mapped[bool] = mapped_column(Boolean, nullable=False)
    requiere_especialidad: Mapped[bool] = mapped_column(Boolean, nullable=False)
    especialidad_predeterminada_id: Mapped[int | None] = mapped_column(
        ForeignKey("especialidades.id", ondelete="RESTRICT", name="fk_actividad_especialidad_id"), nullable=True,
    )
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    especialidad_predeterminada: Mapped["Especialidad | None"] = relationship()
