from datetime import datetime
from pydantic import BaseModel

class PendingReviewItem(BaseModel):
    id: int
    paciente_id: int
    patient_name: str
    title: str
    requested_at: datetime
    submitted_at: datetime | None
    documents_count: int

class PendingReviewResponse(BaseModel):
    count: int
    items: list[PendingReviewItem]
