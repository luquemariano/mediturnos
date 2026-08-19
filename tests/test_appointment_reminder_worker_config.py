import os
import subprocess
import sys

import pytest
from pydantic import ValidationError

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


def test_worker_requires_database_url():
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
