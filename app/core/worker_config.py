from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from app.core.public_url import validar_public_api_url


class AppointmentReminderWorkerSettings(BaseSettings):
    database_url: str
    app_timezone: str = "America/Argentina/Buenos_Aires"
    app_env: Literal["development", "demo", "test", "production"] = "production"
    email_provider: Literal["in_memory", "resend"] = "in_memory"
    resend_api_key: SecretStr | None = None
    email_from: str | None = None
    public_api_url: str = ""
    appointment_action_secret: SecretStr | None = None

    @model_validator(mode="after")
    def validar_configuracion(self) -> "AppointmentReminderWorkerSettings":
        try:
            database = make_url(self.database_url)
        except ArgumentError as error:
            raise ValueError("DATABASE_URL debe ser una URL válida.") from error
        if self.app_env == "production" and database.get_backend_name() != "postgresql":
            raise ValueError("En production, DATABASE_URL debe ser PostgreSQL.")
        if self.email_provider == "resend":
            if not self.resend_api_key or not self.resend_api_key.get_secret_value().strip():
                raise ValueError("RESEND_API_KEY es obligatorio con EMAIL_PROVIDER=resend.")
            if not self.email_from or not self.email_from.strip():
                raise ValueError("EMAIL_FROM es obligatorio con EMAIL_PROVIDER=resend.")
        if self.app_env == "production" and (not self.appointment_action_secret or len(self.appointment_action_secret.get_secret_value().strip()) < 32):
            raise ValueError("En production, APPOINTMENT_ACTION_SECRET debe tener al menos 32 caracteres.")
        if self.app_env == "production" and not self.public_api_url.strip():
            raise ValueError("En production, PUBLIC_API_URL es obligatorio.")
        if self.public_api_url.strip():
            self.public_api_url = validar_public_api_url(self.public_api_url, production=self.app_env == "production")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        hide_input_in_errors=True,
    )


def load_worker_settings() -> AppointmentReminderWorkerSettings:
    return AppointmentReminderWorkerSettings()
