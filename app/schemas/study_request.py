from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
StudyRequestStatus = Literal["pending", "submitted", "reviewed", "closed", "cancelled"]
class StudyRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    instructions: str | None = Field(default=None, max_length=5000)
    turno_id: int | None = None
    expires_at: datetime | None = None
    @field_validator("title")
    @classmethod
    def normalizar_title(cls, value: str) -> str:
        value = value.strip()
        if not value: raise ValueError("El título es obligatorio.")
        return value
    @field_validator("instructions")
    @classmethod
    def normalizar_instructions(cls, value: str | None) -> str | None:
        if value is None: return None
        value = value.strip()
        return value or None
    @field_validator("expires_at")
    @classmethod
    def validar_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None: raise ValueError("La fecha debe incluir timezone.")
        return value
class StudyRequestResponse(BaseModel):
    id: int; paciente_id: int; profesional_id: int; turno_id: int | None; title: str; instructions: str | None; status: StudyRequestStatus; requested_at: datetime; expires_at: datetime | None; submitted_at: datetime | None; reviewed_at: datetime | None; closed_at: datetime | None; cancelled_at: datetime | None; created_at: datetime; updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
StudyRequestListItem = StudyRequestResponse
