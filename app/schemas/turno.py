from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.datetime_utils import a_utc, desde_base_utc


class TurnoCrear(BaseModel):
    paciente_id: int = Field(gt=0)
    prestacion_id: int = Field(gt=0)
    fecha_hora: datetime
    observaciones: str | None = Field(
        default=None,
        max_length=1000,
    )

    @field_validator("fecha_hora")
    @classmethod
    def normalizar_fecha_hora(cls, valor: datetime) -> datetime:
        return a_utc(valor)


class TurnoCrearProfesional(TurnoCrear):
    model_config = ConfigDict(extra="forbid")


class TurnoCrearPropio(BaseModel):
    prestacion_id: int = Field(gt=0)
    fecha_hora: datetime
    observaciones: str | None = Field(
        default=None,
        max_length=1000,
    )

    @field_validator("fecha_hora")
    @classmethod
    def normalizar_fecha_hora(cls, valor: datetime) -> datetime:
        return a_utc(valor)


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

    @field_validator("fecha_hora")
    @classmethod
    def normalizar_fecha_hora(cls, valor: datetime) -> datetime:
        return a_utc(valor)


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

    @field_validator("fecha_hora", mode="before")
    @classmethod
    def agregar_zona_negocio(cls, valor: datetime) -> datetime:
        return desde_base_utc(valor)

    model_config = ConfigDict(
        from_attributes=True,
    )
