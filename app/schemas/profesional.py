from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


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

    matricula: str = Field(
        min_length=3,
        max_length=50,
    )

    telefono: str | None = Field(
        default=None,
        max_length=30,
    )

    email: str | None = Field(
        default=None,
        max_length=150,
    )

    especialidades: list[EspecialidadProfesionalCrear] = Field(
        min_length=1,
    )


class ProfesionalActualizar(BaseModel):
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

    telefono: str | None = Field(
        default=None,
        max_length=30,
    )

    email: str | None = Field(
        default=None,
        max_length=150,
    )

    @field_validator(
        "nombre",
        "apellido",
        "matricula",
    )
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


class ProfesionalRespuesta(BaseModel):
    id: int
    nombre: str
    apellido: str
    matricula: str
    telefono: str | None
    email: str | None
    activo: bool

    model_config = ConfigDict(from_attributes=True)
