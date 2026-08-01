from pydantic import BaseModel, ConfigDict, Field


class EspecialidadCrear(BaseModel):
    nombre: str = Field(
        min_length=2,
        max_length=100,
    )

    descripcion: str | None = None

    duracion_turno_minutos: int = Field(
        default=30,
        ge=10,
        le=180,
    )
    
class EspecialidadCrear(BaseModel):
    nombre: str = Field(
        min_length=2,
        max_length=100,
    )

    descripcion: str | None = None

    duracion_turno_minutos: int = Field(
        default=30,
        ge=10,
        le=180,
    )


class EspecialidadRespuesta(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    duracion_turno_minutos: int
    activa: bool

    model_config = ConfigDict(from_attributes=True)