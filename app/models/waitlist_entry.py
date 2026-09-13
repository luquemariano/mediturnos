from datetime import date, datetime, time, timezone
from uuid import uuid4

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


WAITLIST_STATES = ("activa", "ofertada", "reservada", "cancelada", "vencida")
WAITLIST_ORIGINS = ("profesional", "publico")


class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"
    __table_args__ = (
        CheckConstraint("fecha_hasta >= fecha_desde", name="ck_waitlist_dates"),
        CheckConstraint(
            "(hora_desde IS NULL AND hora_hasta IS NULL) OR "
            "(hora_desde IS NOT NULL AND hora_hasta IS NOT NULL AND hora_hasta > hora_desde)",
            name="ck_waitlist_hours",
        ),
        CheckConstraint("estado IN ('activa', 'ofertada', 'reservada', 'cancelada', 'vencida')", name="ck_waitlist_state"),
        CheckConstraint("origen IN ('profesional', 'publico')", name="ck_waitlist_origin"),
        Index("ix_waitlist_prof_service_state", "profesional_id", "prestacion_id", "estado"),
        Index("ix_waitlist_state_dates", "estado", "fecha_desde", "fecha_hasta"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    identificador_publico: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    profesional_id: Mapped[int] = mapped_column(ForeignKey("profesionales.id"), nullable=False, index=True)
    prestacion_id: Mapped[int] = mapped_column(ForeignKey("prestaciones.id"), nullable=False, index=True)
    paciente_id: Mapped[int] = mapped_column(ForeignKey("pacientes.id"), nullable=False, index=True)
    fecha_desde: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_hasta: Mapped[date] = mapped_column(Date, nullable=False)
    hora_desde: Mapped[time | None] = mapped_column(Time, nullable=True)
    hora_hasta: Mapped[time | None] = mapped_column(Time, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="activa", server_default="activa", index=True)
    origen: Mapped[str] = mapped_column(String(20), nullable=False, default="profesional", server_default="profesional")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    profesional = relationship("Profesional")
    prestacion = relationship("Prestacion")
    paciente = relationship("Paciente")
