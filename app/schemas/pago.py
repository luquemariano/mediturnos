from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PagoRespuesta(BaseModel):
    id: int
    turno_id: int
    preference_id: str | None
    payment_id: str | None
    estado: str
    monto: Decimal
    init_point: str | None
    creado_en: datetime
    actualizado_en: datetime

    model_config = ConfigDict(from_attributes=True)