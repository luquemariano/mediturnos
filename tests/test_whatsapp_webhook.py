import hashlib
import hmac
import json

from pydantic import SecretStr

from app.routers import whatsapp_webhook
from app.services.whatsapp_webhook_service import parse_webhook_events, verify_webhook_signature


SECRET = "test-webhook-app-secret"
VERIFY = "test-verify-token"


def signed(body: bytes, secret=SECRET):
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def enable(monkeypatch, enabled=True):
    monkeypatch.setattr(whatsapp_webhook.settings, "whatsapp_enabled", enabled)
    monkeypatch.setattr(whatsapp_webhook.settings, "whatsapp_verify_token", SecretStr(VERIFY))
    monkeypatch.setattr(whatsapp_webhook.settings, "whatsapp_app_secret", SecretStr(SECRET))


def test_signature_uses_raw_bytes_and_rejects_changes():
    body = b'{"object":"whatsapp_business_account"}'
    assert verify_webhook_signature(body, signed(body), SECRET)
    assert not verify_webhook_signature(body + b" ", signed(body), SECRET)
    assert not verify_webhook_signature(body, None, SECRET)
    assert not verify_webhook_signature(body, signed(body), "wrong")


def test_parser_recognizes_messages_and_statuses_defensively():
    payload = {"object": "whatsapp_business_account", "entry": [{"changes": [{"field": "messages", "value": {"metadata": {"phone_number_id": "test-id"}, "messages": [{"id": "msg-1", "type": "text", "timestamp": "1"}], "statuses": [{"id": "msg-1", "status": "sent", "timestamp": "2"}, {"id": "msg-1", "status": "delivered"}, {"id": "msg-1", "status": "read"}, {"id": "msg-1", "status": "failed"}]}}]}]}
    events = parse_webhook_events(payload)
    assert [event.kind for event in events] == ["message", "status", "status", "status", "status"]
    assert events[0].message_id == "msg-1" and events[1].status == "sent"
    assert parse_webhook_events({"object": "other"}) == []
    assert parse_webhook_events({"object": "whatsapp_business_account"}) == []


def test_get_verification_success_and_failures(monkeypatch):
    enable(monkeypatch)
    response = whatsapp_webhook.verify("subscribe", VERIFY, "challenge-test")
    assert response.status_code == 200 and response.body == b"challenge-test"
    try:
        whatsapp_webhook.verify("subscribe", "wrong", "challenge")
    except Exception as error:
        assert getattr(error, "status_code", None) == 403 and VERIFY not in str(error)
    try:
        whatsapp_webhook.verify("other", VERIFY, "challenge")
    except Exception as error:
        assert getattr(error, "status_code", None) == 403


def test_disabled_get_is_not_operational(monkeypatch):
    enable(monkeypatch, False)
    try:
        whatsapp_webhook.verify("subscribe", VERIFY, "challenge")
    except Exception as error:
        assert getattr(error, "status_code", None) == 404


def test_post_signature_and_invalid_json(monkeypatch):
    enable(monkeypatch)
    body = json.dumps({"object": "whatsapp_business_account", "entry": []}).encode()
    class Request:
        def __init__(self): self.headers = {"x-hub-signature-256": signed(body)}
        async def body(self): return body
    import asyncio
    result = asyncio.run(whatsapp_webhook.receive(Request()))
    assert result == {"received": True, "events": 0}


def test_post_logs_only_safe_message_metadata(monkeypatch, caplog):
    enable(monkeypatch)
    body = json.dumps({"object": "whatsapp_business_account", "entry": [{"changes": [{"field": "messages", "value": {"metadata": {"phone_number_id": "phone-secret"}, "contacts": [{"profile": {"name": "Ana Contacto"}, "wa_id": "5491112345678"}], "messages": [{"id": "msg-safe-1", "type": "text", "text": {"body": "contenido privado"}}]}}]}]}).encode()

    class Request:
        def __init__(self):
            self.headers = {"x-hub-signature-256": signed(body)}

        async def body(self):
            return body

    import asyncio
    with caplog.at_level("INFO", logger="mediturnos.whatsapp_webhook"):
        result = asyncio.run(whatsapp_webhook.receive(Request()))

    logs = caplog.text
    assert result == {"received": True, "events": 1}
    assert "whatsapp_webhook_accepted events=1" in logs
    assert "whatsapp_webhook_event kind=message message_id=msg-safe-1 raw_type=text" in logs
    for value in ("contenido privado", "5491112345678", "Ana Contacto", "phone-secret", SECRET, VERIFY, signed(body)):
        assert value not in logs


def test_post_logs_safe_status_metadata_and_unknown_event_stays_accepted(monkeypatch, caplog):
    enable(monkeypatch)
    body = json.dumps({"object": "whatsapp_business_account", "entry": [{"changes": [{"field": "messages", "value": {"statuses": [{"id": "msg-status-1", "status": "delivered"}, {"id": "msg-unknown-1", "status": "queued"}]}}]}]}).encode()

    class Request:
        def __init__(self):
            self.headers = {"x-hub-signature-256": signed(body)}

        async def body(self):
            return body

    import asyncio
    with caplog.at_level("INFO", logger="mediturnos.whatsapp_webhook"):
        result = asyncio.run(whatsapp_webhook.receive(Request()))

    logs = caplog.text
    assert result == {"received": True, "events": 2}
    assert "whatsapp_webhook_event kind=status message_id=msg-status-1 status=delivered" in logs
    assert "msg-unknown-1" not in logs
