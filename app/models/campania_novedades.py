from datetime import UTC, datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class NovedadProducto(Base):
    __tablename__ = "novedades_producto"
    __table_args__ = (CheckConstraint("prioridad IN ('normal','importante')", name="ck_novedades_producto_prioridad"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    descripcion_corta: Mapped[str] = mapped_column(String(500), nullable=False)
    prioridad: Mapped[str] = mapped_column(String(20), nullable=False, default="normal", server_default="normal")
    cerrada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))


class CampaniaNovedades(Base):
    __tablename__ = "campanias_novedades"
    id: Mapped[int] = mapped_column(primary_key=True)
    asunto: Mapped[str] = mapped_column(String(200), nullable=False)
    preheader: Mapped[str] = mapped_column(String(240), nullable=False)
    mensaje_principal: Mapped[str] = mapped_column(Text, nullable=False)
    novedades_json: Mapped[str] = mapped_column(Text, nullable=False)
    destinatarios_json: Mapped[str] = mapped_column(Text, nullable=False)
    creada_por: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    envio_iniciado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")


class EntregaCampaniaNovedades(Base):
    __tablename__ = "entregas_campanias_novedades"
    __table_args__ = (UniqueConstraint("campania_id", "usuario_id", name="uq_campania_usuario"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    campania_id: Mapped[int] = mapped_column(ForeignKey("campanias_novedades.id", ondelete="CASCADE"), nullable=False, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(150), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(30), nullable=True)
    message_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
