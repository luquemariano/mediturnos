import re

from app.models.paciente import Paciente


def normalize_phone_number(value: str | None) -> str | None:
    """Returns a conservative E.164-like number without a plus sign.

    Argentina local numbers are supported for the common area-code formats;
    already international numbers are preserved after removing decoration.
    Ambiguous or short inputs are rejected instead of guessed.
    """
    if not value or not value.strip():
        return None
    text = value.strip()
    digits = re.sub(r"\D", "", text)
    if not digits:
        return None
    if text.startswith("00"):
        digits = digits[2:]
    if digits.startswith("54"):
        rest = digits[2:]
        if rest.startswith("9"):
            rest = rest[1:]
        if len(rest) == 13 and rest[0:2] in {"11", "15"}:
            rest = rest[2:]
        if not 8 <= len(rest) <= 10:
            return None
        return "54" + rest
    if digits.startswith("0"):
        digits = digits[1:]
    if len(digits) > 10:
        area_end = 2 if digits.startswith("11") else 3
        if digits[area_end:area_end + 2] == "15":
            digits = digits[:area_end] + digits[area_end + 2:]
    if len(digits) == 10:
        return "54" + digits
    if 8 <= len(digits) <= 15 and text.startswith("+"):
        return digits
    return None


def get_whatsapp_recipient(patient: Paciente) -> str | None:
    if not patient.whatsapp_opt_in or patient.whatsapp_opt_out_at is not None:
        return None
    return normalize_phone_number(patient.telefono)
