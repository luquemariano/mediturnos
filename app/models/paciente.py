from datetime import date

from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Paciente(Base):
    __tablename__ = "pacientes"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    apellido: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    dni: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )

    fecha_nacimiento: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    telefono: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    obra_social: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    numero_afiliado: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )