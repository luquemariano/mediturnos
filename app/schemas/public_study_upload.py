from pydantic import BaseModel, ConfigDict, Field

class PublicStudyUploadIntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=1)
    filename: str = Field(min_length=1, max_length=500)
    mime_type: str
    size_bytes: int

class PublicStudyUploadIntentResponse(BaseModel):
    document_id: int
    upload_url: str
    expires_in_seconds: int
    required_content_type: str

class PublicStudyConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=1)

class PublicStudySubmitRequest(PublicStudyConfirmRequest):
    pass

class PublicStudyRemoveRequest(PublicStudyConfirmRequest):
    pass

class PublicStudyUploadedDocument(BaseModel):
    document_id: int
    filename: str
    size_bytes: int

class PublicStudySubmitResponse(BaseModel):
    status: str
    documents: list[PublicStudyUploadedDocument]
