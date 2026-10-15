from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import ahora_utc
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.consultorio import Consultorio
    from app.models.profesional import Profesional


class ConsultorioProfesional(Base):
    """Vínculo preparado para fases futuras; no transfiere identidad ni datos clínicos."""

    __tablename__ = "consultorio_profesionales"
    __table_args__ = (
        UniqueConstraint("consultorio_id", "profesional_id", name="uq_consultorio_profesionales_par"),
        CheckConstraint(
            "estado IN ('preparatorio', 'activo', 'suspendido', 'retirado')",
            name="ck_consultorio_profesionales_estado",
        ),
        CheckConstraint("fecha_baja IS NULL OR fecha_baja >= fecha_alta", name="ck_consultorio_profesionales_fechas"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    consultorio_id: Mapped[int] = mapped_column(
        ForeignKey("consultorios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    profesional_id: Mapped[int] = mapped_column(
        ForeignKey("profesionales.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="preparatorio", server_default="preparatorio")
    fecha_alta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)
    fecha_baja: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    consultorio: Mapped["Consultorio"] = relationship(back_populates="profesionales_asignados")
    profesional: Mapped["Profesional"] = relationship()
