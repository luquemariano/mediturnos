from pydantic import BaseModel, Field


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