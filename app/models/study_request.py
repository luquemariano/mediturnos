from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.connection import Base
if TYPE_CHECKING:
    from app.models.paciente import Paciente
    from app.models.profesional import Profesional
    from app.models.turno import Turno

class StudyRequest(Base):
    __tablename__ = "study_requests"
    __table_args__ = (Index("ix_study_requests_paciente_status_requested", "paciente_id", "status", "requested_at"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False, index=True)
    profesional_id: Mapped[int] = mapped_column(ForeignKey("profesionales.id", ondelete="RESTRICT"), nullable=False, index=True)
    turno_id: Mapped[int | None] = mapped_column(ForeignKey("turnos.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending", index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    paciente: Mapped["Paciente"] = relationship(back_populates="study_requests")
    profesional: Mapped["Profesional"] = relationship(back_populates="study_requests")
    turno: Mapped["Turno | None"] = relationship(back_populates="study_requests")
