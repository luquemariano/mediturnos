from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import ahora_utc
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.cuenta_usuario import CuentaUsuario
    from app.models.profesional import Profesional
    from app.models.suscripcion import Suscripcion


class Cuenta(Base):
    __tablename__ = "cuentas"
    __table_args__ = (CheckConstraint("tipo IN ('individual', 'organizacion')", name="ck_cuentas_tipo"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc, onupdate=ahora_utc)

    membresias: Mapped[list["CuentaUsuario"]] = relationship(back_populates="cuenta", cascade="all, delete-orphan")
    profesionales: Mapped[list["Profesional"]] = relationship(back_populates="cuenta")
    suscripcion: Mapped["Suscripcion | None"] = relationship(back_populates="cuenta", uselist=False, cascade="all, delete-orphan")
