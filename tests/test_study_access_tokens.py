from datetime import UTC, datetime, timedelta

import pytest

from app.services.study_access_token_service import (
    PUBLIC_ERROR,
    StudyAccessTokenError,
    create_study_access_token,
    verify_study_access_token,
)


def test_token_valido_y_scope_independiente():
    issued = datetime(2026, 8, 20, 12, tzinfo=UTC)
    token = create_study_access_token(secret="s" * 40, study_request_id=12, patient_id=34, issued_at=issued)
    payload = verify_study_access_token(secret="s" * 40, token=token, ttl_seconds=3600, now=issued + timedelta(minutes=5))
    assert payload.study_request_id == 12
    assert payload.patient_id == 34
    assert payload.scope == "study_upload"
    raw_payload = __import__("base64").urlsafe_b64decode(token.split(".", 1)[0] + "==")
    assert set(__import__("json").loads(raw_payload)) == {"study_request_id", "patient_id", "scope", "issued_at"}


@pytest.mark.parametrize("mutate", [lambda token: token[:-1], lambda token: token.replace(".", "!", 1), lambda token: token + ".x"])
def test_token_manipulado_rechazado(mutate):
    token = create_study_access_token(secret="s" * 40, study_request_id=1, patient_id=2)
    with pytest.raises(StudyAccessTokenError, match=PUBLIC_ERROR):
        verify_study_access_token(secret="s" * 40, token=mutate(token), ttl_seconds=3600)


def test_token_vencido_futuro_y_secret_incorrecto_rechazados():
    issued = datetime(2026, 8, 20, 12, tzinfo=UTC)
    token = create_study_access_token(secret="s" * 40, study_request_id=1, patient_id=2, issued_at=issued)
    with pytest.raises(StudyAccessTokenError):
        verify_study_access_token(secret="s" * 40, token=token, ttl_seconds=60, now=issued + timedelta(seconds=60))
    with pytest.raises(StudyAccessTokenError):
        verify_study_access_token(secret="s" * 40, token=token, ttl_seconds=3600, now=issued - timedelta(seconds=61),)
    with pytest.raises(StudyAccessTokenError):
        verify_study_access_token(secret="x" * 40, token=token, ttl_seconds=3600, now=issued)
