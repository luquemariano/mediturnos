from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.paciente import Paciente
    from app.models.profesional import Profesional

class ProfesionalPaciente(Base):
    __tablename__ = "profesional_paciente"
    __table_args__ = (UniqueConstraint("profesional_id", "paciente_id", name="uq_profesional_paciente"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    profesional_id: Mapped[int] = mapped_column(ForeignKey("profesionales.id", ondelete="CASCADE"), nullable=False, index=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False, index=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    profesional: Mapped["Profesional"] = relationship(back_populates="pacientes_vinculados")
    paciente: Mapped["Paciente"] = relationship(back_populates="profesionales_vinculados")
