from dataclasses import dataclass
import hashlib
import hmac
from typing import Any


@dataclass(frozen=True)
class WhatsAppWebhookEvent:
    kind: str
    message_id: str | None = None
    status: str | None = None
    phone_number_id: str | None = None
    timestamp: str | None = None
    raw_type: str | None = None
    error_code: int | None = None
    error_title: str | None = None
    error_message: str | None = None


def verify_webhook_signature(raw_body: bytes, signature_header: str | None, app_secret: str) -> bool:
    if not signature_header or not app_secret:
        return False
    prefix, separator, supplied = signature_header.partition("=")
    if prefix != "sha256" or not separator or not supplied:
        return False
    expected = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, supplied)


def parse_webhook_events(payload: Any) -> list[WhatsAppWebhookEvent]:
    if not isinstance(payload, dict) or payload.get("object") != "whatsapp_business_account":
        return []
    events: list[WhatsAppWebhookEvent] = []
    for entry in payload.get("entry") or []:
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes") or []:
            if not isinstance(change, dict) or change.get("field") != "messages":
                continue
            value = change.get("value")
            if not isinstance(value, dict):
                continue
            metadata = value.get("metadata") if isinstance(value.get("metadata"), dict) else {}
            phone_number_id = metadata.get("phone_number_id")
            for message in value.get("messages") or []:
                if isinstance(message, dict):
                    events.append(WhatsAppWebhookEvent("message", message.get("id"), None, phone_number_id, message.get("timestamp"), message.get("type")))
            for status in value.get("statuses") or []:
                if isinstance(status, dict):
                    raw_status = status.get("status")
                    kind = "status" if raw_status in {"sent", "delivered", "read", "failed"} else "unsupported"
                    error_code = None
                    error_title = None
                    error_message = None
                    errors = status.get("errors")
                    if raw_status == "failed" and isinstance(errors, list) and errors and isinstance(errors[0], dict):
                        first_error = errors[0]
                        code = first_error.get("code")
                        error_code = code if isinstance(code, int) and not isinstance(code, bool) else None
                        title = first_error.get("title")
                        error_title = title if isinstance(title, str) else None
                        message = first_error.get("message")
                        error_message = message if isinstance(message, str) else None
                    events.append(WhatsAppWebhookEvent(kind, status.get("id"), raw_status, phone_number_id, status.get("timestamp"), "status", error_code, error_title, error_message))
    return events
