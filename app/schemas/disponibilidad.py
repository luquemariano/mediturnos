from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DisponibilidadCrear(BaseModel):
    profesional_id: int = Field(gt=0)
    dia_semana: int = Field(ge=0, le=6)
    hora_inicio: time
    hora_fin: time

    @model_validator(mode="after")
    def validar_horario(self):
        if self.hora_fin <= self.hora_inicio:
            raise ValueError(
                "La hora de finalización debe ser posterior a la de inicio."
            )

        return self


class DisponibilidadRespuesta(BaseModel):
    id: int
    profesional_id: int
    dia_semana: int
    hora_inicio: time
    hora_fin: time
    activa: bool

    model_config = ConfigDict(from_attributes=True)

class HorarioLibreRespuesta(BaseModel):
    fecha_hora: datetime