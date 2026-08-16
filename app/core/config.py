from ipaddress import ip_address
from typing import Literal

from pydantic import (
    AnyHttpUrl,
    SecretStr,
    TypeAdapter,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


adaptador_origen_http = TypeAdapter(AnyHttpUrl)
JWT_SECRET_ILUSTRATIVO = (
    "reemplazar_por_una_clave_larga_y_aleatoria"
)
LONGITUD_MINIMA_JWT_PRODUCCION = 32


def es_host_loopback(host: str) -> bool:
    host_normalizado = host.lower().rstrip(".")

    if (
        host_normalizado.startswith("[")
        and host_normalizado.endswith("]")
    ):
        host_normalizado = host_normalizado[1:-1]

    if host_normalizado == "localhost":
        return True

    try:
        direccion = ip_address(host_normalizado)
    except ValueError:
        return False

    ipv4_mapeada = getattr(
        direccion,
        "ipv4_mapped",
        None,
    )

    return direccion.is_loopback or (
        ipv4_mapeada is not None
        and ipv4_mapeada.is_loopback
    )


class Settings(BaseSettings):
    app_env: Literal[
        "development",
        "demo",
        "test",
        "production",
    ] = "development"
    database_url: str = "sqlite:///./mediturnos.db"
    app_timezone: str = "America/Argentina/Buenos_Aires"
    cors_allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    mercado_pago_access_token: str = ""
    mercado_pago_webhook_secret: str = ""
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    password_reset_expire_minutes: int = 60
    frontend_url: str = "http://localhost:5173"
    email_provider: Literal["in_memory", "resend"] = "in_memory"
    resend_api_key: SecretStr | None = None
    email_from: str | None = None
    demo_seed_enabled: bool = False
    demo_admin_email: str | None = None
    demo_admin_password: SecretStr | None = None
    demo_admin_reset_password: bool = False
    demo_professional_email: str | None = None
    demo_professional_password: SecretStr | None = None
    demo_professional_reset_password: bool = False
    trust_proxy_headers: bool = False
    rate_limit_window_seconds: int = 60
    rate_limit_register_attempts: int = 5
    rate_limit_login_attempts: int = 15
    rate_limit_password_reset_attempts: int = 3
    reset_admin_token: SecretStr | None = None

    @field_validator(
        "rate_limit_window_seconds",
        "rate_limit_register_attempts",
        "rate_limit_login_attempts",
        "rate_limit_password_reset_attempts",
    )
    @classmethod
    def validar_rate_limit(cls, valor: int) -> int:
        if valor <= 0:
            raise ValueError("Los límites de solicitudes deben ser mayores que cero.")
        return valor

    @field_validator("password_reset_expire_minutes")
    @classmethod
    def validar_expiracion_password_reset(cls, minutos: int) -> int:
        if minutos <= 0:
            raise ValueError("PASSWORD_RESET_EXPIRE_MINUTES debe ser mayor que cero.")
        return minutos

    @field_validator("frontend_url")
    @classmethod
    def validar_frontend_url(cls, valor: str) -> str:
        try:
            adaptador_origen_http.validate_python(valor)
        except ValueError as error:
            raise ValueError("FRONTEND_URL debe ser una URL HTTP o HTTPS válida.") from error
        return valor.rstrip("/")

    @field_validator("cors_allowed_origins")
    @classmethod
    def validar_origenes_cors(
        cls,
        origenes: list[str],
    ) -> list[str]:
        if not origenes:
            raise ValueError(
                "CORS_ALLOWED_ORIGINS no puede ser una lista vacía."
            )

        for origen in origenes:
            if origen == "*":
                raise ValueError(
                    "CORS_ALLOWED_ORIGINS no puede contener '*'."
                )

            try:
                url = adaptador_origen_http.validate_python(origen)
            except ValueError as error:
                raise ValueError(
                    "Cada valor de CORS_ALLOWED_ORIGINS debe ser "
                    "un origen HTTP o HTTPS válido. "
                    f"Valor inválido: {origen!r}."
                ) from error

            if (
                url.username is not None
                or url.password is not None
                or url.path not in (None, "/")
                or origen.endswith("/")
                or url.query is not None
                or url.fragment is not None
            ):
                raise ValueError(
                    "Cada valor de CORS_ALLOWED_ORIGINS debe contener "
                    "solamente esquema, host y puerto opcional; "
                    "no se permiten path, query ni fragment. "
                    f"Valor inválido: {origen!r}."
                )

        return origenes

    @model_validator(mode="after")
    def validar_configuracion_produccion(self) -> "Settings":
        if self.app_env != "production":
            return self

        try:
            url_database = make_url(self.database_url)
        except ArgumentError as error:
            raise ValueError(
                "En production, DATABASE_URL debe ser una URL "
                "PostgreSQL válida."
            ) from error

        if (
            url_database.get_backend_name() != "postgresql"
            or not url_database.database
        ):
            raise ValueError(
                "En production, DATABASE_URL debe ser una URL "
                "PostgreSQL válida; SQLite no está permitido."
            )

        if url_database.drivername == "postgresql":
            self.database_url = url_database.set(
                drivername="postgresql+psycopg"
            ).render_as_string(hide_password=False)
        elif url_database.drivername != "postgresql+psycopg":
            raise ValueError(
                "En production, DATABASE_URL debe usar un driver "
                "PostgreSQL compatible con psycopg."
            )

        if (
            self.jwt_secret_key.strip() == JWT_SECRET_ILUSTRATIVO
            or len(self.jwt_secret_key.strip())
            < LONGITUD_MINIMA_JWT_PRODUCCION
        ):
            raise ValueError(
                "En production, JWT_SECRET_KEY debe ser una clave "
                "propia de al menos 32 caracteres."
            )

        for origen in self.cors_allowed_origins:
            host = adaptador_origen_http.validate_python(
                origen
            ).host

            if host is not None and es_host_loopback(host):
                raise ValueError(
                    "En production, CORS_ALLOWED_ORIGINS no puede "
                    "contener localhost ni direcciones de loopback."
                )

        if self.email_provider != "resend":
            raise ValueError(
                "En production, EMAIL_PROVIDER debe ser 'resend'."
            )
        if (
            self.resend_api_key is None
            or not self.resend_api_key.get_secret_value().strip()
        ):
            raise ValueError(
                "En production con Resend, RESEND_API_KEY es obligatorio."
            )
        if not self.email_from or not self.email_from.strip():
            raise ValueError(
                "En production con Resend, EMAIL_FROM es obligatorio."
            )
        frontend_host = adaptador_origen_http.validate_python(
            self.frontend_url
        ).host
        if frontend_host is not None and es_host_loopback(frontend_host):
            raise ValueError(
                "En production, FRONTEND_URL no puede usar localhost ni loopback."
            )

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        hide_input_in_errors=True,
    )


settings = Settings()
