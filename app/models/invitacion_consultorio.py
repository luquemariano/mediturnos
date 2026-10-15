from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import ahora_utc
from app.database.base import Base


class InvitacionConsultorio(Base):
    __tablename__ = "consultorio_invitaciones"
    __table_args__ = (
        CheckConstraint("estado IN ('preparacion', 'pendiente', 'aceptada', 'revocada', 'expirada')", name="ck_consultorio_invitacion_estado"),
        CheckConstraint("email_normalizado = lower(email_normalizado)", name="ck_consultorio_invitacion_email_normalizado"),
        CheckConstraint(
            "(estado = 'preparacion' AND token_hash IS NULL AND vence_en IS NOT NULL) OR "
            "(estado = 'pendiente' AND token_hash IS NOT NULL AND vence_en IS NOT NULL) OR "
            "(estado = 'aceptada' AND token_hash IS NOT NULL AND vence_en IS NULL AND aceptada_por_usuario_id IS NOT NULL AND aceptada_por_profesional_id IS NOT NULL) OR "
            "(estado IN ('revocada', 'expirada') AND token_hash IS NULL)",
            name="ck_consultorio_invitacion_estado_token",
        ),
        Index(
            "uq_consultorio_invitacion_email_pendiente",
            "consultorio_id", "email_normalizado", unique=True,
            postgresql_where=text("estado IN ('pendiente', 'preparacion')"),
            sqlite_where=text("estado IN ('pendiente', 'preparacion')"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    consultorio_id: Mapped[int] = mapped_column(ForeignKey("consultorios.id", ondelete="CASCADE"), nullable=False, index=True)
    email_normalizado: Mapped[str] = mapped_column(String(254), nullable=False)
    nombre_visible: Mapped[str | None] = mapped_column(String(160), nullable=True)
    token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente", server_default="pendiente")
    invitante_usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    vence_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    aceptada_por_usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=True)
    aceptada_por_profesional_id: Mapped[int | None] = mapped_column(ForeignKey("profesionales.id", ondelete="RESTRICT"), nullable=True)
    revocada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)

    consultorio = relationship("Consultorio")
    invitante = relationship("Usuario", foreign_keys=[invitante_usuario_id])
    aceptada_por = relationship("Usuario", foreign_keys=[aceptada_por_usuario_id])
    profesional = relationship("Profesional", foreign_keys=[aceptada_por_profesional_id])
