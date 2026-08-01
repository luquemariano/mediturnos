from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PrestacionCrear(BaseModel):
    nombre: str = Field(
        min_length=2,
        max_length=120,
    )

    descripcion: str | None = None

    duracion_minutos: int = Field(
        ge=10,
        le=240,
    )

    precio: Decimal = Field(
        ge=0,
        decimal_places=2,
    )

    modalidad: Literal["presencial", "virtual"] = "presencial"

    profesional_id: int = Field(
        gt=0,
    )

    especialidad_id: int = Field(
        gt=0,
    )
class PrestacionActualizar(BaseModel):
    nombre: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
    )

    descripcion: str | None = None

    duracion_minutos: int | None = Field(
        default=None,
        ge=10,
        le=240,
    )

    precio: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
    )

    modalidad: Literal["presencial", "virtual"] | None = None

    activa: bool | None = None

class PrestacionRespuesta(BaseModel):
    id: int
    nombre: str
    descripcion: str | None
    duracion_minutos: int
    precio: Decimal
    modalidad: str
    activa: bool
    profesional_id: int
    especialidad_id: int

    model_config = ConfigDict(from_attributes=True)