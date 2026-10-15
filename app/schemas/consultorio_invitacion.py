from datetime import date, time

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class ModuloInvitacionCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sala_id: int = Field(gt=0)
    dia_semana: int = Field(ge=0, le=6)
    hora_inicio: time
    duracion_minutos: int | None = Field(default=None, ge=1, le=1440)
    vigente_desde: date
    vigente_hasta: date | None = None

    @field_validator("hora_inicio")
    @classmethod
    def hora_civil(cls, value: time) -> time:
        if value.tzinfo is not None and value.utcoffset() is not None:
            raise ValueError("La hora debe ser civil, sin zona horaria.")
        return value.replace(tzinfo=None)

    @model_validator(mode="after")
    def fechas_validas(self):
        if self.vigente_hasta and self.vigente_hasta < self.vigente_desde:
            raise ValueError("La fecha final no puede preceder a la inicial.")
        return self


class InvitacionCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    nombre_visible: str | None = Field(default=None, max_length=160)
    modulos: list[ModuloInvitacionCrear] = Field(min_length=1, max_length=28)


class InvitacionRespuesta(BaseModel):
    id: int
    email: str
    nombre_visible: str | None
    estado: str
    vence_en: object | None
    modulos_reservados: int


class InvitacionAceptacion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=32, max_length=128)


class InvitacionAceptacionRespuesta(BaseModel):
    mensaje: str
    consultorio_id: int
    profesional_vinculado: bool
