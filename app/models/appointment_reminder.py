from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import ahora_utc
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.turno import Turno


class AppointmentReminder(Base):
    __tablename__ = "appointment_reminders"
    __table_args__ = (
        UniqueConstraint(
            "turno_id", "channel", "reminder_type", "appointment_datetime_snapshot",
            name="uq_appointment_reminders_occurrence",
        ),
        Index(
            "ix_appointment_reminders_pending_schedule",
            "status", "scheduled_for",
        ),
        Index(
            "ix_appointment_reminders_status_retry",
            "status", "next_attempt_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    turno_id: Mapped[int] = mapped_column(ForeignKey("turnos.id"), nullable=False, index=True)

    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="email")
    reminder_type: Mapped[str] = mapped_column(String(30), nullable=False, default="24h")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    appointment_datetime_snapshot: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recipient_email_snapshot: Mapped[str] = mapped_column(String(150), nullable=False)
    patient_name_snapshot: Mapped[str] = mapped_column(String(201), nullable=False)
    professional_name_snapshot: Mapped[str] = mapped_column(String(201), nullable=False)
    specialty_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    service_name_snapshot: Mapped[str] = mapped_column(String(120), nullable=False)

    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    skip_reason: Mapped[str | None] = mapped_column(String(40), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(30), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(150), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc, onupdate=ahora_utc)

    turno: Mapped["Turno"] = relationship()
