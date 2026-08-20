import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime

SCOPE = "study_upload"
PUBLIC_ERROR = "El enlace no es válido o ya no está disponible."


class StudyAccessTokenError(ValueError):
    pass


@dataclass(frozen=True)
class StudyAccessPayload:
    study_request_id: int
    patient_id: int
    scope: str
    issued_at: int


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_study_access_token(*, secret: str, study_request_id: int, patient_id: int, issued_at: datetime | None = None) -> str:
    if study_request_id <= 0 or patient_id <= 0:
        raise ValueError("Los identificadores deben ser positivos.")
    issued = issued_at or datetime.now(UTC)
    payload = {"study_request_id": study_request_id, "patient_id": patient_id, "scope": SCOPE, "issued_at": int(issued.timestamp())}
    encoded = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).digest()
    return f"{encoded}.{_b64(signature)}"


def verify_study_access_token(*, token: str, secret: str, ttl_seconds: int, now: datetime | None = None) -> StudyAccessPayload:
    try:
        payload_text, signature_text = token.split(".", 1)
        if not payload_text or not signature_text or "." in signature_text:
            raise StudyAccessTokenError(PUBLIC_ERROR)
        expected = hmac.new(secret.encode(), payload_text.encode(), hashlib.sha256).digest()
        supplied = _decode(signature_text)
        if not hmac.compare_digest(expected, supplied):
            raise StudyAccessTokenError(PUBLIC_ERROR)
        raw = json.loads(_decode(payload_text))
        if raw.get("scope") != SCOPE:
            raise StudyAccessTokenError(PUBLIC_ERROR)
        request_id = raw.get("study_request_id")
        patient_id = raw.get("patient_id")
        issued_at = raw.get("issued_at")
        if not isinstance(request_id, int) or isinstance(request_id, bool) or request_id <= 0:
            raise StudyAccessTokenError(PUBLIC_ERROR)
        if not isinstance(patient_id, int) or isinstance(patient_id, bool) or patient_id <= 0:
            raise StudyAccessTokenError(PUBLIC_ERROR)
        if not isinstance(issued_at, int) or isinstance(issued_at, bool):
            raise StudyAccessTokenError(PUBLIC_ERROR)
        current = int((now or datetime.now(UTC)).timestamp())
        if issued_at > current + 60 or current >= issued_at + ttl_seconds:
            raise StudyAccessTokenError(PUBLIC_ERROR)
        return StudyAccessPayload(request_id, patient_id, SCOPE, issued_at)
    except StudyAccessTokenError:
        raise
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        raise StudyAccessTokenError(PUBLIC_ERROR) from None
