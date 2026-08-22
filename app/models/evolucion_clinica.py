from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.paciente import Paciente
    from app.models.profesional import Profesional
    from app.models.study_review import StudyReview


class EvolucionClinica(Base):
    __tablename__ = "evoluciones_clinicas"
    __table_args__ = (
        Index("ix_evoluciones_clinicas_paciente_created_at", "paciente_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False, index=True)
    profesional_id: Mapped[int] = mapped_column(ForeignKey("profesionales.id", ondelete="RESTRICT"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    study_review_id: Mapped[int | None] = mapped_column(ForeignKey("study_reviews.id", ondelete="SET NULL"), nullable=True, index=True)
    contenido: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    paciente: Mapped["Paciente"] = relationship(back_populates="evoluciones")
    profesional: Mapped["Profesional"] = relationship(back_populates="evoluciones")
    study_review: Mapped["StudyReview | None"] = relationship()

    @property
    def profesional_nombre(self) -> str:
        return f"{self.profesional.nombre} {self.profesional.apellido}"
