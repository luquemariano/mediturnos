from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import ahora_utc
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.consultorio import Consultorio
    from app.models.profesional import Profesional
    from app.models.sala import Sala
    from app.models.usuario import Usuario


class SerieModulo(Base):
    __tablename__ = "consultorio_series_modulo"

    id: Mapped[int] = mapped_column(primary_key=True)
    consultorio_id: Mapped[int] = mapped_column(ForeignKey("consultorios.id", ondelete="CASCADE"), nullable=False, index=True)
    sala_id: Mapped[int] = mapped_column(ForeignKey("consultorio_salas.id", ondelete="RESTRICT"), nullable=False, index=True)
    profesional_id: Mapped[int] = mapped_column(ForeignKey("profesionales.id", ondelete="RESTRICT"), nullable=False, index=True)
    creado_por_usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)

    consultorio: Mapped["Consultorio"] = relationship()
    sala: Mapped["Sala"] = relationship()
    profesional: Mapped["Profesional"] = relationship()
    creado_por: Mapped["Usuario"] = relationship()
