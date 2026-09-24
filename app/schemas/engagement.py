from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PreferenciaNovedadesActualizar(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recibir_novedades_turnelia: bool


class PreferenciaNovedadesRespuesta(BaseModel):
    recibir_novedades_turnelia: bool
    fecha_aceptacion_novedades: datetime | None
    fecha_baja_novedades: datetime | None

    model_config = ConfigDict(from_attributes=True)
