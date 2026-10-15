from datetime import date, datetime, time
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import ahora_utc
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.serie_modulo import SerieModulo


class ReglaRecurrenciaModulo(Base):
    __tablename__ = "consultorio_reglas_modulo"
    __table_args__ = (
        UniqueConstraint("serie_id", "version", name="uq_consultorio_regla_serie_version"),
        Index("ix_consultorio_reglas_modulo_activas", "estado", "vigente_desde", "vigente_hasta"),
        CheckConstraint("dia_semana BETWEEN 0 AND 6", name="ck_consultorio_regla_dia_semana"),
        CheckConstraint("duracion_minutos BETWEEN 1 AND 1440", name="ck_consultorio_regla_duracion"),
        CheckConstraint("vigente_hasta IS NULL OR vigente_hasta >= vigente_desde", name="ck_consultorio_regla_vigencia"),
        CheckConstraint("estado IN ('activa', 'reemplazada', 'cancelada')", name="ck_consultorio_regla_estado"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    serie_id: Mapped[int] = mapped_column(ForeignKey("consultorio_series_modulo.id", ondelete="RESTRICT"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    dia_semana: Mapped[int] = mapped_column(Integer, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time(), nullable=False)
    duracion_minutos: Mapped[int] = mapped_column(Integer, nullable=False)
    zona_horaria: Mapped[str] = mapped_column(String(64), nullable=False)
    vigente_desde: Mapped[date] = mapped_column(Date(), nullable=False)
    vigente_hasta: Mapped[date | None] = mapped_column(Date(), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="activa", server_default="activa")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)

    serie: Mapped["SerieModulo"] = relationship()

    @property
    def sala_id(self) -> int:
        return self.serie.sala_id

    @property
    def profesional_id(self) -> int:
        return self.serie.profesional_id
