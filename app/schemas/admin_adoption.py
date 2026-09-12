from datetime import datetime

from pydantic import BaseModel


class AdminAdoptionItemRespuesta(BaseModel):
    usuario_id: int
    profesional_id: int
    cuenta_id: int
    nombre: str
    apellido: str
    email: str
    first_login_at: datetime | None
    last_login_at: datetime | None
    login_count: int
    last_activity_at: datetime | None
    days_since_last_activity: int | None
    active_days: int
    patients_created: int
    appointments_created: int
    services_created: int
    availabilities_created: int
    clinical_evolutions_created: int
    adoption_status: str
