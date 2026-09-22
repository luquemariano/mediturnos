from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.services.phone_service import get_whatsapp_recipient, normalize_phone_number


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("+54 9 351 123-4567", "5493511234567"),
        ("5493511234567", "5493511234567"),
        ("0351 15 1234567", "5493511234567"),
        ("+1 (202) 555-0100", "12025550100"),
        ("", None),
        ("no es un teléfono", None),
    ],
)
def test_normalize_phone_number(value, expected):
    assert normalize_phone_number(value) == expected


def test_whatsapp_recipient_requires_active_consent_and_valid_phone():
    patient = SimpleNamespace(whatsapp_opt_in=False, whatsapp_opt_out_at=None, telefono="+54 9 351 123-4567")
    assert get_whatsapp_recipient(patient) is None
    patient.whatsapp_opt_in = True
    assert get_whatsapp_recipient(patient) == "5493511234567"
    patient.whatsapp_opt_out_at = datetime.now(UTC)
    assert get_whatsapp_recipient(patient) is None
