from datetime import datetime
from typing import Literal

from pydantic import BaseModel, SecretStr, field_validator


PlanCode = Literal["profesional", "consultorio", "centro"]
EstadoSuscripcion = Literal["trial", "active", "past_due", "cancelled", "expired"]


class IniciarSuscripcionEntrada(BaseModel):
    plan: PlanCode
    card_token_id: SecretStr

    @field_validator("card_token_id")
    @classmethod
    def validar_card_token_id(cls, valor: SecretStr) -> SecretStr:
        token = valor.get_secret_value().strip()
        if not token:
            raise ValueError("card_token_id no puede estar vacío.")
        if len(token) > 255:
            raise ValueError("card_token_id excede la longitud permitida.")
        return SecretStr(token)


class IniciarSuscripcionRespuesta(BaseModel):
    estado: EstadoSuscripcion
    checkout_url: str | None = None


class SuscripcionRespuesta(BaseModel):
    cuenta_id: int
    plan: PlanCode
    estado: EstadoSuscripcion
    trial_started_at: datetime | None
    trial_ends_at: datetime | None
    billing_provider: Literal["manual", "mercadopago"]
    provider_status: str | None
    next_payment_at: datetime | None
    cancelled_at: datetime | None


class OperacionSuscripcionRespuesta(BaseModel):
    procesado: bool
    suscripcion: SuscripcionRespuesta
