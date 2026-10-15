from datetime import date, datetime, time, timedelta, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _hora_civil_sin_zona(value: time) -> time:
    if value.tzinfo is not None and value.utcoffset() is not None:
        raise ValueError("La hora recurrente debe ser hora civil sin zona; se usa la zona del consultorio.")
    return value.replace(tzinfo=None)


class ReglaModuloCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sala_id: int = Field(gt=0)
    profesional_id: int = Field(gt=0)
    dia_semana: int = Field(ge=0, le=6)
    hora_inicio: time
    duracion_minutos: int | None = Field(default=None, ge=1, le=1440)
    vigente_desde: date
    vigente_hasta: date | None = None

    @field_validator("hora_inicio")
    @classmethod
    def validar_hora_civil(cls, value: time) -> time:
        return _hora_civil_sin_zona(value)

    @model_validator(mode="after")
    def validar_periodo(self):
        if self.vigente_hasta is not None and self.vigente_hasta < self.vigente_desde:
            raise ValueError("La fecha final no puede preceder a la fecha inicial.")
        return self


class ReglaModuloActualizacion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vigente_desde: date
    sala_id: int | None = Field(default=None, gt=0)
    profesional_id: int | None = Field(default=None, gt=0)
    dia_semana: int | None = Field(default=None, ge=0, le=6)
    hora_inicio: time | None = None
    duracion_minutos: int | None = Field(default=None, ge=1, le=1440)
    vigente_hasta: date | None = None

    @field_validator("hora_inicio")
    @classmethod
    def validar_hora_civil(cls, value: time | None) -> time | None:
        return _hora_civil_sin_zona(value) if value is not None else value


class ModuloExtraordinarioCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sala_id: int = Field(gt=0)
    profesional_id: int = Field(gt=0)
    fecha_inicio: datetime
    fecha_fin: datetime

    @field_validator("fecha_inicio", "fecha_fin")
    @classmethod
    def exigir_instante_con_zona(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("La fecha debe incluir zona horaria.")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validar_intervalo(self):
        if self.fecha_fin <= self.fecha_inicio:
            raise ValueError("El fin debe ser posterior al inicio.")
        if self.fecha_fin - self.fecha_inicio > timedelta(days=1):
            raise ValueError("Un módulo extraordinario no puede superar 24 horas.")
        return self


class ModuloOcurrenciaActualizar(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sala_id: int | None = Field(default=None, gt=0)
    profesional_id: int | None = Field(default=None, gt=0)
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None

    @field_validator("fecha_inicio", "fecha_fin")
    @classmethod
    def normalizar_instante(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("La fecha debe incluir zona horaria.")
            return value.astimezone(timezone.utc)
        return value

    @model_validator(mode="after")
    def validar_alguna_modificacion(self):
        if not self.model_fields_set:
            raise ValueError("Debe indicar al menos un cambio.")
        return self


class ModuloOcurrenciaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sala_id: int
    sala_nombre: str
    profesional_id: int
    profesional_nombre: str
    fecha_inicio: datetime
    fecha_fin: datetime
    fecha_origen: date | None
    estado: str
    origen: str


class ReglaModuloRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    serie_id: int
    sala_id: int
    profesional_id: int
    version: int
    dia_semana: int
    hora_inicio: time
    duracion_minutos: int
    zona_horaria: str
    vigente_desde: date
    vigente_hasta: date | None
    estado: str
