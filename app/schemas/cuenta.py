from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class CuentaActualRespuesta(BaseModel):
    cuenta_id: int
    plan: Literal["profesional", "consultorio", "centro"]
    subscription_status: Literal["trial", "active", "past_due", "cancelled", "expired"]
    trial_started_at: datetime | None
    trial_ends_at: datetime | None
    trial_days_remaining: int
