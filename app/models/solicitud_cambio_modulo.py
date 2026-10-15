from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.datetime_utils import ahora_utc
from app.database.base import Base


class SolicitudCambioModulo(Base):
    """Auditoría mínima de cambios bloqueados; no contiene datos de pacientes."""

    __tablename__ = "consultorio_solicitudes_cambio_modulo"
    __table_args__ = (
        CheckConstraint("turnos_afectados >= 0", name="ck_consultorio_cambio_turnos_no_negativos"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    consultorio_id: Mapped[int] = mapped_column(ForeignKey("consultorios.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    ocurrencia_id: Mapped[int | None] = mapped_column(ForeignKey("consultorio_ocurrencias_modulo.id", ondelete="RESTRICT"), nullable=True)
    regla_id: Mapped[int | None] = mapped_column(ForeignKey("consultorio_reglas_modulo.id", ondelete="RESTRICT"), nullable=True)
    accion: Mapped[str] = mapped_column(String(30), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="bloqueada", server_default="bloqueada")
    turnos_afectados: Mapped[int] = mapped_column(Integer, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)
