from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import ahora_utc
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.cuenta import Cuenta
    from app.models.consultorio_administrador import ConsultorioAdministrador
    from app.models.consultorio_profesional import ConsultorioProfesional
    from app.models.sala import Sala


class Consultorio(Base):
    __tablename__ = "consultorios"
    __table_args__ = (
        CheckConstraint("duracion_modulo_minutos > 0", name="ck_consultorios_duracion_modulo_positiva"),
        CheckConstraint("horizonte_materializacion_dias > 0", name="ck_consultorios_horizonte_positivo"),
        CheckConstraint("cupo_profesionales >= 1", name="ck_consultorios_cupo_profesionales"),
        CheckConstraint("invitacion_expiracion_dias BETWEEN 1 AND 30", name="ck_consultorios_invitacion_expiracion"),
        CheckConstraint("cupo_profesionales >= 1", name="ck_consultorios_cupo_profesionales"),
        CheckConstraint("estado IN ('activo', 'suspendido')", name="ck_consultorios_estado"),
        UniqueConstraint("cuenta_id", name="uq_consultorios_cuenta_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cuenta_id: Mapped[int] = mapped_column(
        ForeignKey("cuentas.id", ondelete="RESTRICT"), nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    zona_horaria: Mapped[str] = mapped_column(String(64), nullable=False, default="America/Argentina/Buenos_Aires")
    duracion_modulo_minutos: Mapped[int] = mapped_column(Integer, nullable=False, default=240, server_default="240")
    horizonte_materializacion_dias: Mapped[int] = mapped_column(Integer, nullable=False, default=90, server_default="90")
    cupo_profesionales: Mapped[int] = mapped_column(Integer, nullable=False, default=4, server_default="4")
    invitacion_expiracion_dias: Mapped[int] = mapped_column(Integer, nullable=False, default=7, server_default="7")
    cupo_profesionales: Mapped[int] = mapped_column(Integer, nullable=False, default=4, server_default="4")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="activo", server_default="activo")
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)

    cuenta: Mapped["Cuenta"] = relationship()
    salas: Mapped[list["Sala"]] = relationship(back_populates="consultorio", cascade="all, delete-orphan")
    administradores: Mapped[list["ConsultorioAdministrador"]] = relationship(
        back_populates="consultorio", cascade="all, delete-orphan"
    )
    profesionales_asignados: Mapped[list["ConsultorioProfesional"]] = relationship(
        back_populates="consultorio", cascade="all, delete-orphan"
    )
