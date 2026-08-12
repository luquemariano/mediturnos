from typing import Literal

from pydantic import AnyHttpUrl, SecretStr, TypeAdapter, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


adaptador_origen_http = TypeAdapter(AnyHttpUrl)


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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
