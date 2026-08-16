from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import ahora_utc
from app.database.connection import Base

if TYPE_CHECKING:
    from app.models.cuenta import Cuenta
    from app.models.suscripcion import Suscripcion
    from app.models.usuario import Usuario


class EventoSuscripcion(Base):
    __tablename__ = "eventos_suscripcion"
    __table_args__ = (
        CheckConstraint("actor_tipo IN ('usuario', 'sistema')", name="ck_eventos_suscripcion_actor_tipo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cuenta_id: Mapped[int] = mapped_column(ForeignKey("cuentas.id", ondelete="CASCADE"), nullable=False, index=True)
    suscripcion_id: Mapped[int] = mapped_column(ForeignKey("suscripciones.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    actor_tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    accion: Mapped[str] = mapped_column(String(50), nullable=False)
    estado_anterior: Mapped[str | None] = mapped_column(String(30), nullable=True)
    estado_nuevo: Mapped[str | None] = mapped_column(String(30), nullable=True)
    plan_anterior: Mapped[str | None] = mapped_column(String(30), nullable=True)
    plan_nuevo: Mapped[str | None] = mapped_column(String(30), nullable=True)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)

    cuenta: Mapped["Cuenta"] = relationship()
    suscripcion: Mapped["Suscripcion"] = relationship()
    actor_usuario: Mapped["Usuario | None"] = relationship()
