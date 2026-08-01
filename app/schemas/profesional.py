from pydantic import BaseModel, ConfigDict, Field


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

    especialidad_ids: list[int] = Field(
        min_length=1,
    )


class ProfesionalRespuesta(BaseModel):
    id: int
    nombre: str
    apellido: str
    matricula: str
    telefono: str | None
    email: str | None
    activo: bool

    model_config = ConfigDict(from_attributes=True)
    
    