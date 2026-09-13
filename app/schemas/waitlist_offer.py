from datetime import datetime
from typing import Literal
from pydantic import BaseModel

class WaitlistOfferResponse(BaseModel):
    estado: Literal["activa", "aceptada", "vencida", "cancelada"]
    profesional: str
    prestacion: str
    fecha_hora: datetime
    expires_at: datetime
    paciente: str
