from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


if TYPE_CHECKING:
    from app.models.cuenta import Cuenta
    from app.models.evolucion_clinica import EvolucionClinica
    from app.models.clinical_profile import ClinicalProfile
    from app.models.study_request import StudyRequest
    from app.models.study_review import StudyReview
    from app.models.profesional_paciente import ProfesionalPaciente
    from app.models.profesional_especialidad import ProfesionalEspecialidad
    from app.models.usuario import Usuario


class Profesional(Base):
    __tablename__ = "profesionales"
    __table_args__ = (
        CheckConstraint(
            "onboarding_step IN ('perfil', 'prestaciones', 'disponibilidad', 'listo', 'completado')",
            name="ck_profesionales_onboarding_step",
        ),
    )

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

    cuenta_id: Mapped[int] = mapped_column(
        ForeignKey("cuentas.id"), nullable=False, index=True,
    )

    nombre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    apellido: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    matricula: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    telefono: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    especialidades_asignadas: Mapped[
        list["ProfesionalEspecialidad"]
    ] = relationship(
        back_populates="profesional",
        cascade="all, delete-orphan",
    )

    usuario: Mapped["Usuario | None"] = relationship(
        back_populates="profesional",
    )

    cuenta: Mapped["Cuenta"] = relationship(back_populates="profesionales")

    onboarding_step: Mapped[str] = mapped_column(
        String(30), nullable=False, default="completado",
        server_default="completado",
    )
    pacientes_vinculados: Mapped[list["ProfesionalPaciente"]] = relationship(back_populates="profesional", cascade="all, delete-orphan")
    evoluciones: Mapped[list["EvolucionClinica"]] = relationship(back_populates="profesional")
    clinical_profiles_updated: Mapped[list["ClinicalProfile"]] = relationship(back_populates="updated_by_profesional")
    study_requests: Mapped[list["StudyRequest"]] = relationship(back_populates="profesional")
    study_reviews: Mapped[list["StudyReview"]] = relationship(back_populates="profesional")
