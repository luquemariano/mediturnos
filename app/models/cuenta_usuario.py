from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import ahora_utc
from app.database.base import Base

if TYPE_CHECKING:
    from app.models.cuenta import Cuenta
    from app.models.usuario import Usuario


class CuentaUsuario(Base):
    __tablename__ = "cuentas_usuarios"
    __table_args__ = (CheckConstraint("rol_cuenta IN ('propietario', 'administrador', 'miembro')", name="ck_cuentas_usuarios_rol"),)

    cuenta_id: Mapped[int] = mapped_column(ForeignKey("cuentas.id", ondelete="CASCADE"), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    rol_cuenta: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=ahora_utc)

    cuenta: Mapped["Cuenta"] = relationship(back_populates="membresias")
    usuario: Mapped["Usuario"] = relationship(back_populates="membresias_cuenta")
