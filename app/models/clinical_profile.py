from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base
if TYPE_CHECKING:
    from app.models.paciente import Paciente
    from app.models.profesional import Profesional

class ClinicalProfile(Base):
    __tablename__ = "clinical_profiles"
    __table_args__ = (UniqueConstraint("paciente_id", name="uq_clinical_profiles_paciente_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False, index=True)
    antecedentes: Mapped[str | None] = mapped_column(Text, nullable=True)
    alergias: Mapped[str | None] = mapped_column(Text, nullable=True)
    medicacion_habitual: Mapped[str | None] = mapped_column(Text, nullable=True)
    condiciones_relevantes: Mapped[str | None] = mapped_column(Text, nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_by_profesional_id: Mapped[int | None] = mapped_column(ForeignKey("profesionales.id", ondelete="SET NULL"), nullable=True, index=True)
    paciente: Mapped["Paciente"] = relationship(back_populates="clinical_profile")
    updated_by_profesional: Mapped["Profesional | None"] = relationship(back_populates="clinical_profiles_updated")
