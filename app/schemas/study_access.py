from datetime import datetime
from pydantic import BaseModel, ConfigDict


class StudyAccessLinkResponse(BaseModel):
    url: str
    expires_in_seconds: int


class PublicStudyRequestResponse(BaseModel):
    study_request_id: int
    professional_name: str
    title: str
    instructions: str | None
    requested_at: datetime
    expires_at: datetime | None
    status: str
    model_config = ConfigDict(from_attributes=True)
