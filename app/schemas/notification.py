from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    message: str
    entity_type: str
    entity_id: int
    read_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    unread_count: int
