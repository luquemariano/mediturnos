from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


if TYPE_CHECKING:
    from app.models.evolucion_clinica import EvolucionClinica
    from app.models.clinical_profile import ClinicalProfile
    from app.models.patient_document import PatientDocument
    from app.models.profesional_paciente import ProfesionalPaciente
    from app.models.usuario import Usuario


class Paciente(Base):
    __tablename__ = "pacientes"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    usuario_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"),
        unique=True,
        nullable=True,
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

    dni: Mapped[str | None] = mapped_column(
        String(20),
        unique=True,
        nullable=True,
    )

    fecha_nacimiento: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    telefono: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
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

    usuario: Mapped["Usuario | None"] = relationship(
        back_populates="paciente",
    )
    profesionales_vinculados: Mapped[list["ProfesionalPaciente"]] = relationship(back_populates="paciente", cascade="all, delete-orphan")
    evoluciones: Mapped[list["EvolucionClinica"]] = relationship(back_populates="paciente", cascade="all, delete-orphan")
    clinical_profile: Mapped["ClinicalProfile | None"] = relationship(back_populates="paciente", uselist=False, cascade="all, delete-orphan")
    patient_documents: Mapped[list["PatientDocument"]] = relationship(back_populates="paciente", cascade="all, delete-orphan")
