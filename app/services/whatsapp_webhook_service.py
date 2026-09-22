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
                    events.append(WhatsAppWebhookEvent(kind, status.get("id"), raw_status, phone_number_id, status.get("timestamp"), "status"))
    return events
