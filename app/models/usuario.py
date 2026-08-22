from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.cuenta_usuario import CuentaUsuario
    from app.models.paciente import Paciente
    from app.models.password_reset_token import PasswordResetToken
    from app.models.profesional import Profesional

class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    rol: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="paciente",
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    creado_en: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )
    
    paciente: Mapped["Paciente | None"] = relationship(
        back_populates="usuario",
        uselist=False,
    )

    profesional: Mapped["Profesional | None"] = relationship(
        back_populates="usuario",
        uselist=False,
    )

    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="usuario",
        cascade="all, delete-orphan",
    )

    membresias_cuenta: Mapped[list["CuentaUsuario"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan",
    )


Index("ix_usuarios_email_lower_unique", func.lower(Usuario.email), unique=True)
