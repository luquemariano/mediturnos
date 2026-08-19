import base64
import hashlib
import hmac
import json
import time
from datetime import UTC, datetime, timedelta


TOKEN_TTL = timedelta(hours=48)
SCOPES = {"confirm", "cancel"}


class AppointmentActionTokenError(ValueError):
    pass


def _encode(value: dict, secret: str) -> str:
    payload = base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).decode().rstrip("=")
    signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest()
    return f"{payload}.{base64.urlsafe_b64encode(signature).decode().rstrip('=')}"


def generate_appointment_action_token(*, secret: str, turno_id: int, appointment_datetime_snapshot: datetime, action_scope: str, issued_at: datetime | None = None) -> str:
    if action_scope not in SCOPES:
        raise ValueError("Scope de acción inválido.")
    issued = issued_at or datetime.now(UTC)
    payload = {"turno_id": turno_id, "snapshot": appointment_datetime_snapshot.isoformat(), "scope": action_scope, "issued_at": int(issued.timestamp())}
    return _encode(payload, secret)


def verify_appointment_action_token(*, token: str, secret: str, expected_scope: str, now: datetime | None = None) -> dict:
    try:
        payload_text, signature_text = token.split(".", 1)
        expected = hmac.new(secret.encode(), payload_text.encode(), hashlib.sha256).digest()
        supplied = base64.urlsafe_b64decode(signature_text + "=" * (-len(signature_text) % 4))
        if not hmac.compare_digest(expected, supplied):
            raise AppointmentActionTokenError("invalid_token")
        payload = json.loads(base64.urlsafe_b64decode(payload_text + "=" * (-len(payload_text) % 4)))
        if payload.get("scope") != expected_scope:
            raise AppointmentActionTokenError("invalid_scope")
        current = (now or datetime.now(UTC)).timestamp()
        if current > int(payload["issued_at"]) + int(TOKEN_TTL.total_seconds()):
            raise AppointmentActionTokenError("expired")
        return payload
    except AppointmentActionTokenError:
        raise
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise AppointmentActionTokenError("invalid_token") from error
