from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)
from app.schemas.actividad_profesional import ActividadProfesionalRespuesta
from typing import Literal

OnboardingStep = Literal["perfil", "prestaciones", "disponibilidad", "listo", "completado"]


class EspecialidadProfesionalCrear(BaseModel):
    especialidad_id: int = Field(
        gt=0,
    )

    duracion_turno_minutos: int = Field(
        ge=10,
        le=180,
    )


class ProfesionalCrear(BaseModel):
    nombre: str = Field(
        min_length=2,
        max_length=100,
    )

    apellido: str = Field(
        min_length=2,
        max_length=100,
    )

    actividad_profesional_id: int = Field(gt=0)

    matricula: str | None = Field(
        default=None,
        max_length=50,
    )

    telefono: str | None = Field(
        default=None,
        max_length=30,
    )

    email: EmailStr | None = Field(
        default=None,
        max_length=150,
    )

    especialidad_id: int | None = Field(default=None, gt=0)
    especialidades: list[EspecialidadProfesionalCrear] | None = Field(default=None, min_length=1)

    @field_validator("matricula", mode="before")
    @classmethod
    def normalizar_matricula(cls, valor: str | None) -> str | None:
        return valor.strip() or None if isinstance(valor, str) else valor

    @field_validator("actividad_profesional_id")
    @classmethod
    def validar_actividad_no_anulable(cls, valor: int | None) -> int:
        if valor is None:
            raise ValueError("La actividad no se puede quitar de un perfil clasificado.")
        return valor


class ProfesionalActualizar(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    apellido: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    matricula: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )

    actividad_profesional_id: int | None = Field(default=None, gt=0)

    telefono: str | None = Field(
        default=None,
        max_length=30,
    )

    email: EmailStr | None = Field(
        default=None,
        max_length=150,
    )

    especialidades: list[
        EspecialidadProfesionalCrear
    ] | None = Field(
        default=None,
        min_length=1,
    )

    @field_validator("nombre", "apellido")
    @classmethod
    def validar_campos_requeridos(
        cls,
        valor: str | None,
    ) -> str:
        if valor is None:
            raise ValueError(
                "El campo no puede ser nulo."
            )

        return valor

    @field_validator("matricula", mode="before")
    @classmethod
    def normalizar_matricula(cls, valor: str | None) -> str | None:
        return valor.strip() or None if isinstance(valor, str) else valor

    @field_validator("actividad_profesional_id")
    @classmethod
    def validar_actividad_no_anulable(cls, valor: int | None) -> int:
        if valor is None:
            raise ValueError("La actividad no se puede quitar de un perfil clasificado.")
        return valor

    @field_validator("especialidades")
    @classmethod
    def validar_especialidades_requeridas(
        cls,
        valor: list[
            EspecialidadProfesionalCrear
        ] | None,
    ) -> list[EspecialidadProfesionalCrear]:
        if valor is None:
            raise ValueError(
                "El campo no puede ser nulo."
            )

        return valor


class EspecialidadProfesionalRespuesta(BaseModel):
    especialidad_id: int
    duracion_turno_minutos: int | None

    model_config = ConfigDict(from_attributes=True)


class ProfesionalRespuesta(BaseModel):
    id: int
    nombre: str
    apellido: str
    matricula: str | None
    actividad_profesional_id: int | None = None
    actividad_profesional: ActividadProfesionalRespuesta | None = None
    telefono: str | None
    email: str | None
    activo: bool
    onboarding_step: OnboardingStep
    especialidades: list[
        EspecialidadProfesionalRespuesta
    ] = Field(
        validation_alias="especialidades_asignadas",
    )

    model_config = ConfigDict(from_attributes=True)
