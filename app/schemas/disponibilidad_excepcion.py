from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DisponibilidadExcepcionCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha: date
    tipo: Literal["cierre_dia", "franja_extraordinaria"]
    hora_inicio: time | None = None
    hora_fin: time | None = None

    @model_validator(mode="after")
    def validar_tipo_y_horario(self):
        if self.tipo == "cierre_dia":
            if self.hora_inicio is not None or self.hora_fin is not None:
                raise ValueError("Un cierre de día no debe incluir horas.")
        elif self.hora_inicio is None or self.hora_fin is None:
            raise ValueError("El horario especial requiere hora de inicio y finalización.")
        elif self.hora_fin <= self.hora_inicio:
            raise ValueError("La hora de finalización debe ser posterior a la de inicio.")
        return self


class DisponibilidadExcepcionRespuesta(BaseModel):
    id: int
    profesional_id: int
    fecha: date
    tipo: str
    origen: str
    nombre: str | None
    hora_inicio: time | None
    hora_fin: time | None
    activa: bool

    model_config = ConfigDict(from_attributes=True)


class DisponibilidadExcepcionRango(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha_desde: date
    fecha_hasta: date

    @model_validator(mode="after")
    def validar_rango(self):
        if self.fecha_hasta < self.fecha_desde:
            raise ValueError("La fecha hasta debe ser igual o posterior a la fecha desde.")
        if (self.fecha_hasta - self.fecha_desde).days + 1 > 365:
            raise ValueError("El período no puede superar los 365 días.")
        return self


class DisponibilidadExcepcionRangoCreadoRespuesta(BaseModel):
    creados: int
    ya_existentes: int


class DisponibilidadExcepcionRangoReabiertoRespuesta(BaseModel):
    reabiertos: int


class FeriadoCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fecha: date
    tipo: Literal["feriado", "no_laborable"]
    nombre: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def normalizar_nombre(self):
        if self.nombre is not None:
            self.nombre = self.nombre.strip() or None
        return self
