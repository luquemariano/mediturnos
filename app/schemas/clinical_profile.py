from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator
class ClinicalProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    antecedentes: str | None = None
    alergias: str | None = None
    medicacion_habitual: str | None = None
    condiciones_relevantes: str | None = None
    observaciones: str | None = None
    @field_validator("antecedentes", "alergias", "medicacion_habitual", "condiciones_relevantes", "observaciones")
    @classmethod
    def normalizar_texto(cls, value: str | None) -> str | None:
        if value is None: return None
        value = value.strip()
        return value or None
class ClinicalProfileResponse(BaseModel):
    id: int | None = None
    paciente_id: int
    antecedentes: str | None = None
    alergias: str | None = None
    medicacion_habitual: str | None = None
    condiciones_relevantes: str | None = None
    observaciones: str | None = None
    updated_at: datetime | None = None
    updated_by_profesional_id: int | None = None
    model_config = ConfigDict(from_attributes=True)
