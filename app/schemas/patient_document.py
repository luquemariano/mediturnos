from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

DocumentCategory = Literal["laboratory", "imaging", "order", "report", "prescription", "other"]

class PatientDocumentUploadIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filename: str = Field(min_length=1, max_length=500)
    mime_type: str
    size_bytes: int
    category: DocumentCategory

class PatientDocumentUploadIntentResponse(BaseModel):
    document_id: int
    upload_url: str
    expires_in_seconds: int
    required_content_type: str

class PatientDocumentResponse(BaseModel):
    id: int
    paciente_id: int
    original_filename: str
    mime_type: str
    size_bytes: int | None
    category: str
    status: str
    created_at: datetime
    available_at: datetime | None
    uploaded_by_profesional_id: int | None
    model_config = ConfigDict(from_attributes=True)

class PatientDocumentDownloadUrlResponse(BaseModel):
    download_url: str
    expires_in_seconds: int
