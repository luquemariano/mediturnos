from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class WaitlistOffer(Base):
    __tablename__ = "waitlist_offers"
    __table_args__ = (
        CheckConstraint("estado IN ('activa','aceptada','vencida','cancelada')", name="ck_waitlist_offer_state"),
        Index("ix_waitlist_offers_state_expires", "estado", "expires_at"),
        Index("ix_waitlist_offers_slot_state", "profesional_id", "prestacion_id", "slot_inicio", "estado"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    identificador_publico: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    waitlist_entry_id: Mapped[int] = mapped_column(ForeignKey("waitlist_entries.id"), nullable=False, index=True)
    profesional_id: Mapped[int] = mapped_column(ForeignKey("profesionales.id"), nullable=False)
    prestacion_id: Mapped[int] = mapped_column(ForeignKey("prestaciones.id"), nullable=False)
    slot_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    slot_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="activa", server_default="activa")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    entry = relationship("WaitlistEntry")
