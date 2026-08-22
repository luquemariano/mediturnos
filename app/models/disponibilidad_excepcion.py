from datetime import date, time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, Index, String, Time, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.profesional import Profesional


class DisponibilidadExcepcion(Base):
    __tablename__ = "disponibilidades_excepciones"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('cierre_dia', 'franja_extraordinaria')",
            name="ck_disponibilidad_excepcion_tipo",
        ),
        CheckConstraint(
            "origen IN ('legacy', 'manual', 'vacaciones', 'feriado', 'no_laborable')",
            name="ck_disponibilidad_excepcion_origen",
        ),
        CheckConstraint(
            "(tipo = 'cierre_dia' AND hora_inicio IS NULL AND hora_fin IS NULL) OR "
            "(tipo = 'franja_extraordinaria' AND hora_inicio IS NOT NULL "
            "AND hora_fin IS NOT NULL AND hora_fin > hora_inicio)",
            name="ck_disponibilidad_excepcion_horario",
        ),
        Index(
            "ix_disponibilidad_excepcion_profesional_fecha_activa",
            "profesional_id", "fecha", "activa",
        ),
        Index(
            "uq_disponibilidad_excepcion_cierre_activo",
            "profesional_id", "fecha", "origen",
            unique=True,
            postgresql_where=text("activa AND tipo = 'cierre_dia'"),
            sqlite_where=text("activa = 1 AND tipo = 'cierre_dia'"),
        ),
        Index(
            "uq_disponibilidad_excepcion_feriado_activo",
            "profesional_id", "fecha",
            unique=True,
            postgresql_where=text("activa AND tipo = 'cierre_dia' AND origen IN ('feriado', 'no_laborable')"),
            sqlite_where=text("activa = 1 AND tipo = 'cierre_dia' AND origen IN ('feriado', 'no_laborable')"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    profesional_id: Mapped[int] = mapped_column(ForeignKey("profesionales.id"), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    origen: Mapped[str] = mapped_column(String(30), nullable=False, default="manual", server_default="manual")
    nombre: Mapped[str | None] = mapped_column(String(120), nullable=True)
    hora_inicio: Mapped[time | None] = mapped_column(Time, nullable=True)
    hora_fin: Mapped[time | None] = mapped_column(Time, nullable=True)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    profesional: Mapped["Profesional"] = relationship()
