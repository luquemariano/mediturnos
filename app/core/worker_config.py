from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from app.core.public_url import validar_public_api_url


class AppointmentReminderWorkerSettings(BaseSettings):
    database_url: str
    app_timezone: str = "America/Argentina/Buenos_Aires"
    app_env: Literal["development", "demo", "test", "staging", "production"] = "production"
    email_provider: Literal["in_memory", "resend"] = "in_memory"
    resend_api_key: SecretStr | None = None
    email_from: str | None = None
    public_api_url: str = ""
    appointment_action_secret: SecretStr | None = None
    whatsapp_enabled: bool = False
    whatsapp_provider: Literal["fake", "meta"] = "fake"
    whatsapp_api_version: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_business_account_id: str | None = None
    whatsapp_access_token: SecretStr | None = None
    whatsapp_verify_token: SecretStr | None = None
    whatsapp_app_secret: SecretStr | None = None
    staging_email_send_enabled: bool = False
    staging_email_allowlist: str = ""
    staging_whatsapp_meta_enabled: bool = False
    staging_whatsapp_meta_test_number_confirmed: bool = False
    staging_whatsapp_phone_number_id_allowlist: str = ""
    staging_whatsapp_business_account_id_allowlist: str = ""
    staging_whatsapp_recipient_allowlist: str = ""
    waitlist_offer_worker_interval_seconds: int = 60

    @model_validator(mode="after")
    def validar_configuracion(self) -> "AppointmentReminderWorkerSettings":
        if self.waitlist_offer_worker_interval_seconds <= 0:
            raise ValueError("WAITLIST_OFFER_WORKER_INTERVAL_SECONDS debe ser positivo.")
        if self.app_env == "production" and (
            self.staging_email_send_enabled or self.staging_whatsapp_meta_enabled
            or self.staging_whatsapp_meta_test_number_confirmed
            or self.staging_email_allowlist.strip()
            or self.staging_whatsapp_phone_number_id_allowlist.strip()
            or self.staging_whatsapp_business_account_id_allowlist.strip()
            or self.staging_whatsapp_recipient_allowlist.strip()
        ):
            raise ValueError("La configuración exclusiva de comunicaciones de staging no se admite en production.")
        try:
            database = make_url(self.database_url)
        except ArgumentError as error:
            raise ValueError("DATABASE_URL debe ser una URL válida.") from error
        if self.app_env == "production" and database.get_backend_name() != "postgresql":
            raise ValueError("En production, DATABASE_URL debe ser PostgreSQL.")
        if self.app_env == "staging":
            if (
                database.get_backend_name() != "postgresql"
                or database.host != "db"
                or database.database != "turnelia_staging"
            ):
                raise ValueError("En staging, DATABASE_URL debe usar PostgreSQL aislado turnelia_staging en db.")
            self.database_url = database.set(drivername="postgresql+psycopg").render_as_string(hide_password=False)
        if self.email_provider == "resend":
            if not self.resend_api_key or not self.resend_api_key.get_secret_value().strip():
                raise ValueError("RESEND_API_KEY es obligatorio con EMAIL_PROVIDER=resend.")
            if not self.email_from or not self.email_from.strip():
                raise ValueError("EMAIL_FROM es obligatorio con EMAIL_PROVIDER=resend.")
        if self.whatsapp_enabled and self.whatsapp_provider == "meta":
            missing = [
                name
                for name, value in (
                    ("WHATSAPP_API_VERSION", self.whatsapp_api_version),
                    ("WHATSAPP_PHONE_NUMBER_ID", self.whatsapp_phone_number_id),
                    ("WHATSAPP_ACCESS_TOKEN", self.whatsapp_access_token),
                )
                if value is None
                or not (
                    value.get_secret_value()
                    if isinstance(value, SecretStr)
                    else str(value)
                ).strip()
            ]
            if missing:
                raise ValueError(
                    "Con WHATSAPP_ENABLED=true y WHATSAPP_PROVIDER=meta, "
                    "faltan configuración: " + ", ".join(missing) + "."
                )
        if self.app_env == "production" and (not self.appointment_action_secret or len(self.appointment_action_secret.get_secret_value().strip()) < 32):
            raise ValueError("En production, APPOINTMENT_ACTION_SECRET debe tener al menos 32 caracteres.")
        if self.app_env == "production" and not self.public_api_url.strip():
            raise ValueError("En production, PUBLIC_API_URL es obligatorio.")
        if self.app_env == "staging":
            if self.staging_email_send_enabled:
                if self.email_provider != "resend" or not self.resend_api_key or not self.resend_api_key.get_secret_value().strip() or not self.email_from or not self._email_allowlist():
                    raise ValueError("El email real de staging requiere Resend, remitente y allowlist.")
            elif self.email_provider != "in_memory":
                raise ValueError("En staging EMAIL_PROVIDER debe ser in_memory salvo habilitación explícita.")
            if self.staging_whatsapp_meta_enabled:
                if not self.whatsapp_enabled or self.whatsapp_provider != "meta" or not self.staging_whatsapp_meta_test_number_confirmed:
                    raise ValueError("WhatsApp Meta staging requiere habilitación y confirmación explícitas.")
                if not self.staging_whatsapp_recipient_allowlist.strip():
                    raise ValueError("STAGING_WHATSAPP_RECIPIENT_ALLOWLIST es obligatorio.")
                if not self.whatsapp_verify_token or not self.whatsapp_verify_token.get_secret_value().strip() or not self.whatsapp_app_secret or not self.whatsapp_app_secret.get_secret_value().strip():
                    raise ValueError("WhatsApp Meta staging requiere secretos dedicados de webhook.")
                if self.public_api_url.rstrip("/") != "https://api.staging.turnelia.com.ar":
                    raise ValueError("WhatsApp Meta staging requiere el webhook HTTPS dedicado.")
                phone_ids = {item.strip() for item in self.staging_whatsapp_phone_number_id_allowlist.split(",") if item.strip()}
                if not self.whatsapp_phone_number_id or self.whatsapp_phone_number_id not in phone_ids:
                    raise ValueError("El ID de teléfono debe coincidir con la allowlist de staging.")
                business_ids = {item.strip() for item in self.staging_whatsapp_business_account_id_allowlist.split(",") if item.strip()}
                if not self.whatsapp_business_account_id or self.whatsapp_business_account_id not in business_ids:
                    raise ValueError("El ID de cuenta comercial debe coincidir con la allowlist de staging.")
                if not self.obtener_staging_whatsapp_recipient_allowlist():
                    raise ValueError("STAGING_WHATSAPP_RECIPIENT_ALLOWLIST debe incluir teléfonos autorizados.")
            elif self.whatsapp_enabled or self.whatsapp_provider != "fake":
                raise ValueError("En staging, WhatsApp debe permanecer deshabilitado con proveedor fake.")
            elif any(secret is not None and secret.get_secret_value().strip() for secret in (self.whatsapp_access_token, self.whatsapp_verify_token, self.whatsapp_app_secret)):
                raise ValueError("En staging no se admiten credenciales Meta sin habilitación explícita.")
        if self.public_api_url.strip():
            self.public_api_url = validar_public_api_url(self.public_api_url, production=self.app_env == "production")
        return self

    def _email_allowlist(self) -> frozenset[str]:
        from pydantic import EmailStr, TypeAdapter
        adapter = TypeAdapter(EmailStr)
        values = set()
        try:
            for item in self.staging_email_allowlist.split(","):
                if item.strip():
                    values.add(str(adapter.validate_python(item.strip())).lower())
        except ValueError as error:
            raise ValueError("STAGING_EMAIL_ALLOWLIST contiene una dirección inválida.") from error
        return frozenset(values)

    def obtener_staging_email_allowlist(self) -> frozenset[str]:
        return self._email_allowlist()

    def obtener_staging_whatsapp_recipient_allowlist(self) -> frozenset[str]:
        from app.services.phone_service import normalize_phone_number
        values = set()
        for item in self.staging_whatsapp_recipient_allowlist.split(","):
            if item.strip():
                normalized = normalize_phone_number(item.strip())
                if normalized is None:
                    raise ValueError("STAGING_WHATSAPP_RECIPIENT_ALLOWLIST contiene un teléfono inválido.")
                values.add(normalized)
        return frozenset(values)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        hide_input_in_errors=True,
    )


def load_worker_settings() -> AppointmentReminderWorkerSettings:
    return AppointmentReminderWorkerSettings()
