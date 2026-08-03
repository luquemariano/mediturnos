from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TurnoCrear(BaseModel):
    paciente_id: int = Field(gt=0)
    prestacion_id: int = Field(gt=0)
    fecha_hora: datetime
    observaciones: str | None = Field(
        default=None,
        max_length=1000,
    )


class TurnoCrearPropio(BaseModel):
    prestacion_id: int = Field(gt=0)
    fecha_hora: datetime
    observaciones: str | None = Field(
        default=None,
        max_length=1000,
    )


class TurnoActualizarEstado(BaseModel):
    estado: Literal[
        "reservado",
        "confirmado",
        "cancelado",
        "ausente",
        "finalizado",
    ]


class TurnoReprogramar(BaseModel):
    fecha_hora: datetime


class TurnoRespuesta(BaseModel):
    id: int

    paciente_id: int
    paciente_nombre: str

    prestacion_id: int
    prestacion_nombre: str

    profesional_nombre: str

    especialidad_nombre: str

    fecha_hora: datetime

    estado: str

    observaciones: str | None

    model_config = ConfigDict(
        from_attributes=True,
    )