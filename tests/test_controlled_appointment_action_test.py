import pytest

from app.scripts import create_controlled_appointment_action_test as script


def test_requires_explicit_production_flag(monkeypatch):
    monkeypatch.delenv("CONTROLLED_PRODUCTION_TEST", raising=False)
    with pytest.raises(SystemExit, match="CONTROLLED_PRODUCTION_TEST"):
        script._require_environment()


def test_requires_recipient(monkeypatch):
    monkeypatch.setenv("CONTROLLED_PRODUCTION_TEST", "true")
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("CONTROLLED_TEST_EMAIL", raising=False)
    with pytest.raises(SystemExit, match="CONTROLLED_TEST_EMAIL"):
        script._require_environment()


def test_rejects_invalid_recipient(monkeypatch):
    monkeypatch.setenv("CONTROLLED_PRODUCTION_TEST", "true")
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CONTROLLED_TEST_EMAIL", "not-an-email")
    with pytest.raises(SystemExit, match="no es válido"):
        script._require_environment()
