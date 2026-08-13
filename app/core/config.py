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
    demo_seed_enabled: bool = False
    demo_admin_email: str | None = None
    demo_admin_password: SecretStr | None = None
    demo_admin_reset_password: bool = False
    demo_professional_email: str | None = None
    demo_professional_password: SecretStr | None = None
    demo_professional_reset_password: bool = False

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

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        hide_input_in_errors=True,
    )


settings = Settings()
