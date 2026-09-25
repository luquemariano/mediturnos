from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class NovedadEntrada(BaseModel):
    titulo: str = Field(min_length=2, max_length=180)
    descripcion_corta: str = Field(min_length=2, max_length=500)
    prioridad: Literal["normal", "importante"] = "normal"
    cerrada: bool = False
    activa: bool = True
    model_config = ConfigDict(extra="forbid")


class NovedadRespuesta(NovedadEntrada):
    id: int
    creado_en: datetime
    actualizado_en: datetime
    model_config = ConfigDict(from_attributes=True)


class CampaniaEntrada(BaseModel):
    asunto: str = Field(min_length=2, max_length=200)
    preheader: str = Field(min_length=2, max_length=240)
    mensaje_principal: str = Field(min_length=2, max_length=10000)
    novedades_ids: list[int] = Field(default_factory=list)
    todos: bool = True
    destinatarios_ids: list[int] = Field(default_factory=list)
    idempotency_key: str = Field(min_length=12, max_length=100)
    model_config = ConfigDict(extra="forbid")


class ConfirmarEnvio(BaseModel):
    confirmar: Literal[True]
    model_config = ConfigDict(extra="forbid")


class TokenBajaEntrada(BaseModel):
    token: str = Field(min_length=20, max_length=2048)
    model_config = ConfigDict(extra="forbid")
