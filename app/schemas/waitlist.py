from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class WaitlistEntryCreate(BaseModel):
    prestacion_id: int = Field(gt=0)
    paciente_id: int = Field(gt=0)
    fecha_desde: date
    fecha_hasta: date
    hora_desde: time | None = None
    hora_hasta: time | None = None

    @model_validator(mode="after")
    def validar_rango(self):
        if self.fecha_hasta < self.fecha_desde:
            raise ValueError("La fecha hasta no puede ser anterior a la fecha desde.")
        if (self.hora_desde is None) != (self.hora_hasta is None):
            raise ValueError("Debe indicar ambas horas o ninguna.")
        if self.hora_desde is not None and self.hora_hasta <= self.hora_desde:
            raise ValueError("La hora hasta debe ser posterior a la hora desde.")
        return self


class WaitlistEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    identificador_publico: str
    paciente_id: int
    paciente_nombre: str
    prestacion_id: int
    prestacion_nombre: str
    fecha_desde: date
    fecha_hasta: date
    hora_desde: time | None
    hora_hasta: time | None
    estado: Literal["activa", "ofertada", "reservada", "cancelada", "vencida"]
    origen: Literal["profesional", "publico"]
    created_at: datetime
    updated_at: datetime
