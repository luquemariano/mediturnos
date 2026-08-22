from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, BigInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
if TYPE_CHECKING:
    from app.models.paciente import Paciente
    from app.models.profesional import Profesional
    from app.models.study_request import StudyRequest

class PatientDocument(Base):
    __tablename__ = "patient_documents"
    __table_args__ = (UniqueConstraint("storage_key", name="uq_patient_documents_storage_key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False, index=True)
    study_request_id: Mapped[int | None] = mapped_column(ForeignKey("study_requests.id", ondelete="SET NULL"), nullable=True, index=True)
    origin: Mapped[str] = mapped_column(String(20), nullable=False, default="professional")
    uploaded_by_profesional_id: Mapped[int | None] = mapped_column(ForeignKey("profesionales.id", ondelete="SET NULL"), nullable=True, index=True)
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by_profesional_id: Mapped[int | None] = mapped_column(ForeignKey("profesionales.id", ondelete="SET NULL"), nullable=True)
    paciente: Mapped["Paciente"] = relationship(back_populates="patient_documents")
    study_request: Mapped["StudyRequest | None"] = relationship(back_populates="patient_documents")
    uploaded_by_profesional: Mapped["Profesional | None"] = relationship(foreign_keys=[uploaded_by_profesional_id])
    deleted_by_profesional: Mapped["Profesional | None"] = relationship(foreign_keys=[deleted_by_profesional_id])
