import os
import subprocess
import sys

import pytest
from pydantic import SecretStr, ValidationError

from app.core.worker_config import AppointmentReminderWorkerSettings


def _worker_environment() -> dict[str, str]:
    return {
        "DATABASE_URL": "sqlite:///./worker-test.db",
        "APP_ENV": "test",
        "APP_TIMEZONE": "America/Argentina/Buenos_Aires",
        "EMAIL_PROVIDER": "in_memory",
    }


def test_worker_imports_without_web_settings(monkeypatch):
    environment = os.environ.copy()
    environment.update(_worker_environment())
    for name in (
        "JWT_SECRET_KEY", "CORS_ALLOWED_ORIGINS", "FRONTEND_URL",
        "JWT_ALGORITHM", "JWT_EXPIRE_MINUTES", "PASSWORD_RESET_EXPIRE_MINUTES",
        "TRUST_PROXY_HEADERS",
    ):
        environment.pop(name, None)
    for name in tuple(environment):
        if name.startswith("RATE_LIMIT_"):
            environment.pop(name, None)

    result = subprocess.run(
        [sys.executable, "-c", "import app.scripts.process_appointment_reminders; print('worker starts successfully')"],
        cwd=os.getcwd(),
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "worker starts successfully" in result.stdout


def test_worker_requires_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    environment = _worker_environment()
    environment.pop("DATABASE_URL")
    with pytest.raises(ValidationError):
        AppointmentReminderWorkerSettings(_env_file=None, **environment)


def test_worker_requires_resend_credentials():
    with pytest.raises(ValidationError):
        AppointmentReminderWorkerSettings(
            database_url="sqlite:///./worker-test.db",
            app_env="test",
            email_provider="resend",
            email_from="verified@example.com",
        )


def test_worker_meta_config_completa_es_valida_y_token_es_secreto():
    settings = AppointmentReminderWorkerSettings(
        _env_file=None,
        database_url="sqlite:///./worker-test.db",
        app_env="test",
        whatsapp_enabled=True,
        whatsapp_provider="meta",
        whatsapp_api_version="v99.0",
        whatsapp_phone_number_id="test-phone-id",
        whatsapp_access_token="test-access-token",
    )

    assert settings.whatsapp_api_version == "v99.0"
    assert settings.whatsapp_phone_number_id == "test-phone-id"
    assert isinstance(settings.whatsapp_access_token, SecretStr)
    assert "test-access-token" not in repr(settings)


def test_worker_meta_habilitado_requiere_las_tres_credenciales():
    with pytest.raises(ValidationError, match="WHATSAPP_API_VERSION.*WHATSAPP_PHONE_NUMBER_ID.*WHATSAPP_ACCESS_TOKEN"):
        AppointmentReminderWorkerSettings(
            _env_file=None,
            database_url="sqlite:///./worker-test.db",
            app_env="test",
            whatsapp_enabled=True,
            whatsapp_provider="meta",
        )


@pytest.mark.parametrize(
    "values",
    (
        {"whatsapp_enabled": False, "whatsapp_provider": "meta"},
        {"whatsapp_enabled": True, "whatsapp_provider": "fake"},
    ),
)
def test_worker_sin_meta_no_requiere_credenciales(values):
    settings = AppointmentReminderWorkerSettings(
        _env_file=None,
        database_url="sqlite:///./worker-test.db",
        app_env="test",
        **values,
    )

    assert settings.whatsapp_access_token is None


@pytest.mark.parametrize("url", ["", "not-a-url", "http://localhost:8000", "http://127.0.0.1:8000", "https://api.example.com/path?x=1", "https://api.example.com/#fragment", "https://user:pass@api.example.com"])
def test_worker_rejects_invalid_production_public_api_url(url):
    with pytest.raises(ValidationError):
        AppointmentReminderWorkerSettings(
            _env_file=None,
            database_url="postgresql+psycopg://user:pass@db.example.com/app",
            app_env="production",
            email_provider="resend",
            resend_api_key="r" * 40,
            email_from="Turnelia <no-reply@example.com>",
            appointment_action_secret="a" * 40,
            public_api_url=url,
        )


def test_worker_normalizes_valid_production_public_api_url():
    settings = AppointmentReminderWorkerSettings(
        _env_file=None,
        database_url="postgresql+psycopg://user:pass@db.example.com/app",
        app_env="production",
        email_provider="resend",
        resend_api_key="r" * 40,
        email_from="Turnelia <no-reply@example.com>",
        appointment_action_secret="a" * 40,
        public_api_url="https://api.turnelia.com.ar/",
    )
    assert settings.public_api_url == "https://api.turnelia.com.ar"
