from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class EvolucionClinicaCrear(BaseModel):
    contenido: str

    @field_validator("contenido")
    @classmethod
    def validar_contenido(cls, contenido: str) -> str:
        contenido_limpio = contenido.strip()
        if not contenido_limpio:
            raise ValueError("La evolución debe incluir contenido.")
        return contenido_limpio


class EvolucionClinicaRespuesta(BaseModel):
    id: int
    paciente_id: int
    profesional_id: int
    profesional_nombre: str
    contenido: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
