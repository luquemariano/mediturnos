from datetime import UTC, datetime, timedelta

import pytest

from app.services.appointment_action_token_service import (
    AppointmentActionTokenError,
    generate_appointment_action_token,
    verify_appointment_action_token,
)


def test_confirm_and_cancel_tokens_are_scoped_and_signed():
    issued = datetime(2026, 8, 19, tzinfo=UTC)
    confirm = generate_appointment_action_token(secret="s" * 40, turno_id=7, appointment_datetime_snapshot=issued, action_scope="confirm", issued_at=issued)
    cancel = generate_appointment_action_token(secret="s" * 40, turno_id=7, appointment_datetime_snapshot=issued, action_scope="cancel", issued_at=issued)
    assert verify_appointment_action_token(token=confirm, secret="s" * 40, expected_scope="confirm", now=issued)["turno_id"] == 7
    assert verify_appointment_action_token(token=cancel, secret="s" * 40, expected_scope="cancel", now=issued)["scope"] == "cancel"
    with pytest.raises(AppointmentActionTokenError):
        verify_appointment_action_token(token=confirm, secret="s" * 40, expected_scope="cancel", now=issued)


def test_token_rejects_tampering_and_expiration():
    issued = datetime(2026, 8, 19, tzinfo=UTC)
    token = generate_appointment_action_token(secret="s" * 40, turno_id=7, appointment_datetime_snapshot=issued, action_scope="confirm", issued_at=issued)
    with pytest.raises(AppointmentActionTokenError):
        verify_appointment_action_token(token=token[:-1] + "x", secret="s" * 40, expected_scope="confirm", now=issued)
    with pytest.raises(AppointmentActionTokenError):
        verify_appointment_action_token(token=token, secret="s" * 40, expected_scope="confirm", now=issued + timedelta(hours=49))
