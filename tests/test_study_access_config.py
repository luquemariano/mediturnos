import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings


def test_configuracion_study_access_por_defecto_es_independiente_y_ttl_valido():
    config = Settings(_env_file=None, jwt_secret_key="test-secret")
    assert config.study_access_token_ttl_seconds == 2592000
    assert config.study_access_secret.get_secret_value() != config.appointment_action_secret.get_secret_value()
    assert "turnelia-local-study-access-secret" not in repr(config)


def test_ttl_study_access_debe_ser_positivo():
    with pytest.raises(ValidationError, match="STUDY_ACCESS_TOKEN_TTL_SECONDS"):
        Settings(_env_file=None, jwt_secret_key="test-secret", study_access_token_ttl_seconds=0)


def test_secret_production_debe_ser_largo():
    with pytest.raises(ValidationError, match="STUDY_ACCESS_SECRET"):
        Settings(_env_file=None, app_env="production", jwt_secret_key="j" * 40, study_access_secret=SecretStr("short"), database_url="postgresql+psycopg://u:p@db:5432/db", cors_allowed_origins=["https://app.example.com"], email_provider="resend", resend_api_key=SecretStr("r"), email_from="noreply@example.com", appointment_action_secret=SecretStr("a" * 40), public_api_url="https://api.example.com", frontend_url="https://app.example.com")
