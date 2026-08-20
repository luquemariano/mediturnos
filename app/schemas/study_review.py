from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, field_validator

Disposition = Literal["online_response", "requires_in_person", "requires_teleconsultation"]

class StudyReviewCreate(BaseModel):
    review_text: str
    disposition: Disposition
    model_config = ConfigDict(extra="forbid")

    @field_validator("review_text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("La devolución debe incluir contenido.")
        if len(value) > 10000:
            raise ValueError("La devolución no puede superar 10000 caracteres.")
        return value

class StudyReviewResponse(BaseModel):
    id: int
    study_request_id: int
    review_text: str
    disposition: Disposition
    reviewed_at: datetime
    professional_name: str

    model_config = ConfigDict(from_attributes=True)
