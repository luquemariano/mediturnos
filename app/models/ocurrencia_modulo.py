from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import ahora_utc
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.consultorio import Consultorio
    from app.models.regla_recurrencia_modulo import ReglaRecurrenciaModulo
    from app.models.serie_modulo import SerieModulo
    from app.models.sala import Sala
    from app.models.profesional import Profesional
    from app.models.usuario import Usuario
    from app.models.invitacion_consultorio import InvitacionConsultorio


class OcurrenciaModulo(Base):
    __tablename__ = "consultorio_ocurrencias_modulo"
    __table_args__ = (
        CheckConstraint("(profesional_id IS NOT NULL) <> (invitacion_id IS NOT NULL)", name="ck_consultorio_ocurrencia_destino_unico"),
        CheckConstraint("fecha_fin > fecha_inicio", name="ck_consultorio_ocurrencia_intervalo"),
        CheckConstraint("estado IN ('activa', 'suspendida', 'cancelada')", name="ck_consultorio_ocurrencia_estado"),
        CheckConstraint("origen IN ('recurrente', 'extraordinaria', 'excepcion')", name="ck_consultorio_ocurrencia_origen"),
        UniqueConstraint("regla_id", "fecha_origen", name="uq_consultorio_ocurrencia_regla_fecha"),
        Index("ix_consultorio_ocurrencia_sala_inicio", "sala_id", "fecha_inicio"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    consultorio_id: Mapped[int] = mapped_column(ForeignKey("consultorios.id", ondelete="CASCADE"), nullable=False, index=True)
    serie_id: Mapped[int | None] = mapped_column(ForeignKey("consultorio_series_modulo.id", ondelete="RESTRICT"), nullable=True, index=True)
    regla_id: Mapped[int | None] = mapped_column(ForeignKey("consultorio_reglas_modulo.id", ondelete="RESTRICT"), nullable=True, index=True)
    sala_id: Mapped[int] = mapped_column(ForeignKey("consultorio_salas.id", ondelete="RESTRICT"), nullable=False, index=True)
    profesional_id: Mapped[int | None] = mapped_column(ForeignKey("profesionales.id", ondelete="RESTRICT"), nullable=True, index=True)
    invitacion_id: Mapped[int | None] = mapped_column(ForeignKey("consultorio_invitaciones.id", ondelete="RESTRICT"), nullable=True, index=True)
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fecha_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fecha_origen: Mapped[date | None] = mapped_column(Date(), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="activa", server_default="activa")
    origen: Mapped[str] = mapped_column(String(20), nullable=False)
    creado_por_usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)

    consultorio: Mapped["Consultorio"] = relationship()
    serie: Mapped["SerieModulo | None"] = relationship()
    regla: Mapped["ReglaRecurrenciaModulo | None"] = relationship()
    sala: Mapped["Sala"] = relationship()
    profesional: Mapped["Profesional | None"] = relationship()
    invitacion: Mapped["InvitacionConsultorio | None"] = relationship()
    creado_por: Mapped["Usuario | None"] = relationship()

    @property
    def sala_nombre(self) -> str:
        return self.sala.nombre

    @property
    def profesional_nombre(self) -> str:
        if self.profesional is not None:
            return f"{self.profesional.nombre} {self.profesional.apellido}"
        return self.invitacion.nombre_visible if self.invitacion and self.invitacion.nombre_visible else "Invitación pendiente"
