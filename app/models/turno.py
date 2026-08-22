from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    select,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


if TYPE_CHECKING:
    from app.models.paciente import Paciente
    from app.models.prestacion import Prestacion
    from app.models.profesional import Profesional
    from app.models.study_request import StudyRequest


class Turno(Base):
    __tablename__ = "turnos"
    __table_args__ = (
        CheckConstraint(
            "fecha_fin > fecha_hora",
            name="ck_turnos_fecha_fin_posterior",
        ),
        Index(
            "ix_turnos_profesional_fecha_hora",
            "profesional_id",
            "fecha_hora",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    paciente_id: Mapped[int] = mapped_column(
        ForeignKey("pacientes.id"),
        nullable=False,
    )

    prestacion_id: Mapped[int] = mapped_column(
        ForeignKey("prestaciones.id"),
        nullable=False,
    )

    profesional_id: Mapped[int] = mapped_column(
        ForeignKey("profesionales.id"),
        nullable=False,
        default=lambda contexto: _profesional_id_prestacion(
            contexto
        ),
    )

    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    fecha_fin: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda contexto: _fecha_fin_prestacion(
            contexto
        ),
    )

    estado: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="reservado",
    )

    observaciones: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    paciente: Mapped["Paciente"] = relationship()

    prestacion: Mapped["Prestacion"] = relationship()

    profesional: Mapped["Profesional"] = relationship()
    study_requests: Mapped[list["StudyRequest"]] = relationship(back_populates="turno")

    @property
    def paciente_nombre(self) -> str:
        return (
            f"{self.paciente.nombre} "
            f"{self.paciente.apellido}"
        )

    @property
    def prestacion_nombre(self) -> str:
        return self.prestacion.nombre

    @property
    def profesional_nombre(self) -> str:
        return (
            f"{self.profesional.nombre} "
            f"{self.profesional.apellido}"
        )

    @property
    def especialidad_nombre(self) -> str:
        return self.prestacion.especialidad.nombre


def _datos_prestacion(contexto) -> tuple[int, int]:
    from app.models.prestacion import Prestacion

    prestacion_id = contexto.get_current_parameters()[
        "prestacion_id"
    ]
    fila = contexto.connection.execute(
        select(
            Prestacion.profesional_id,
            Prestacion.duracion_minutos,
        ).where(Prestacion.id == prestacion_id)
    ).one()

    return fila.profesional_id, fila.duracion_minutos


def _profesional_id_prestacion(contexto) -> int:
    profesional_id, _ = _datos_prestacion(contexto)

    return profesional_id


def _fecha_fin_prestacion(contexto) -> datetime:
    _, duracion_minutos = _datos_prestacion(contexto)
    fecha_hora = contexto.get_current_parameters()[
        "fecha_hora"
    ]

    return fecha_hora + timedelta(minutes=duracion_minutos)
