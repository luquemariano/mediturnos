import pytest
from pydantic import SecretStr

from app.core.config import Settings


def base_settings(**overrides):
    values = {"_env_file": None, "jwt_secret_key": "test-secret"}
    values.update(overrides)
    return Settings(**values)


def test_whatsapp_deshabilitado_no_requiere_credenciales():
    config = base_settings()

    assert config.whatsapp_enabled is False
    assert config.whatsapp_provider == "fake"
    assert config.whatsapp_access_token is None


def test_whatsapp_fake_habilitado_no_requiere_credenciales_meta():
    config = base_settings(whatsapp_enabled=True, whatsapp_provider="fake")

    assert config.whatsapp_enabled is True
    assert config.whatsapp_provider == "fake"


def test_whatsapp_meta_habilitado_requiere_configuracion_minima():
    with pytest.raises(ValueError, match="WHATSAPP_PHONE_NUMBER_ID"):
        base_settings(whatsapp_enabled=True, whatsapp_provider="meta")


def test_whatsapp_meta_acepta_secretos_sin_exponerlos():
    config = base_settings(
        whatsapp_enabled=True,
        whatsapp_provider="meta",
        whatsapp_phone_number_id="phone-id-test",
        whatsapp_access_token=SecretStr("access-token-test"),
        whatsapp_verify_token=SecretStr("verify-token-test"),
        whatsapp_api_version="configurable-version",
    )

    assert config.whatsapp_access_token.get_secret_value() == "access-token-test"
    assert "access-token-test" not in repr(config)
    assert config.whatsapp_business_account_id is None


def test_whatsapp_meta_rechaza_secretos_vacios():
    with pytest.raises(ValueError, match="WHATSAPP_ACCESS_TOKEN"):
        base_settings(
            whatsapp_enabled=True,
            whatsapp_provider="meta",
            whatsapp_phone_number_id="phone-id-test",
            whatsapp_access_token=SecretStr(""),
            whatsapp_verify_token=SecretStr("verify-token-test"),
            whatsapp_api_version="configurable-version",
        )


def test_whatsapp_provider_valida_valores_conocidos():
    with pytest.raises(ValueError):
        base_settings(whatsapp_provider="unknown")
