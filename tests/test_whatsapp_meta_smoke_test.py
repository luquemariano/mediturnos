from types import SimpleNamespace

import pytest
from pydantic import SecretStr

from app.integrations.messaging import MessageDeliveryResult, MessagingProviderError
from app.scripts import send_whatsapp_meta_smoke_test as smoke


TOKEN = "test-smoke-token-DO-NOT-LEAK"


def configured(monkeypatch):
    monkeypatch.setenv("WHATSAPP_ENABLED", "true")
    monkeypatch.setenv("WHATSAPP_PROVIDER", "meta")
    monkeypatch.setenv("WHATSAPP_API_VERSION", "vTEST")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "test-phone-id")
    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", TOKEN)


def test_dry_run_does_not_call_provider(monkeypatch, capsys):
    configured(monkeypatch)
    called = []
    monkeypatch.setattr(smoke, "_provider", lambda *args: called.append(args))
    assert smoke.main(["--recipient", "12025550100"]) == 0
    output = capsys.readouterr().out
    assert not called and "SEND: disabled" in output and "12025550100" not in output and TOKEN not in output


@pytest.mark.parametrize("field", ["whatsapp_enabled", "whatsapp_provider", "whatsapp_api_version", "whatsapp_phone_number_id", "whatsapp_access_token"])
def test_invalid_configuration_rejected(monkeypatch, capsys, field):
    configured(monkeypatch)
    env_field = {"whatsapp_enabled": "WHATSAPP_ENABLED", "whatsapp_provider": "WHATSAPP_PROVIDER", "whatsapp_api_version": "WHATSAPP_API_VERSION", "whatsapp_phone_number_id": "WHATSAPP_PHONE_NUMBER_ID", "whatsapp_access_token": "WHATSAPP_ACCESS_TOKEN"}[field]
    monkeypatch.setenv(env_field, "false" if field == "whatsapp_enabled" else ("fake" if field == "whatsapp_provider" else ""))
    assert smoke.main(["--recipient", "12025550100"]) == 1
    assert TOKEN not in capsys.readouterr().err


def test_invalid_recipient_rejected(monkeypatch):
    configured(monkeypatch)
    assert smoke.main(["--recipient", "not-a-number"]) == 2


def test_send_uses_meta_provider_once_and_minimal_message(monkeypatch, capsys):
    configured(monkeypatch)
    calls = []
    class Provider:
        def send(self, message):
            calls.append(message)
            assert message.message_type == "meta_smoke_test" and message.payload == {}
            return MessageDeliveryResult(True, "meta_whatsapp", "wamid.test")
        def close(self): pass
    monkeypatch.setattr(smoke, "_provider", lambda *args: Provider())
    assert smoke.main(["--recipient", "12025550100", "--send"]) == 0
    assert len(calls) == 1 and "wamid.test" in capsys.readouterr().out


def test_provider_failure_returns_three_and_does_not_leak(monkeypatch, capsys):
    configured(monkeypatch)
    class Provider:
        def send(self, message): raise MessagingProviderError(f"provider failed {TOKEN}")
        def close(self): pass
    monkeypatch.setattr(smoke, "_provider", lambda *args: Provider())
    assert smoke.main(["--recipient", "12025550100", "--send"]) == 3
    assert TOKEN not in capsys.readouterr().err
