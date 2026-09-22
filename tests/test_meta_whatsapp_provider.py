import httpx
import pytest
from pydantic import SecretStr

from app.integrations.messaging import (
    DEFAULT_TEMPLATE_MAPPING,
    FakeMessagingProvider,
    MetaWhatsAppProvider,
    MessagingConfigurationError,
    MessagingProviderError,
    OutboundMessage,
    get_messaging_provider,
)
from app.integrations.messaging.meta_whatsapp import MetaTemplateDefinition


TOKEN = "test-meta-secret-token-DO-NOT-LEAK"


def message(message_type="appointment_reminder_v1"):
    return OutboundMessage(
        channel="whatsapp", recipient="5493511234567", message_type=message_type,
        payload={"appointment_datetime": "2026-09-23T10:00:00+00:00", "professional_name": "Profesional de prueba", "confirm_token": "fake-confirm-token", "cancel_token": "fake-cancel-token"},
    )


TEMPLATE_MAPPING = {
    "appointment_reminder_v1": MetaTemplateDefinition(
        name="test_appointment_reminder_template",
        language_code="es_AR",
        body_parameter_keys=("appointment_datetime", "professional_name"),
        button_parameter_keys=("confirm_token", "cancel_token"),
    ),
}


def provider(handler):
    transport = httpx.MockTransport(handler)
    return MetaWhatsAppProvider(api_version="v99.0", phone_number_id="test-phone-number-id", access_token=SecretStr(TOKEN), template_mapping=TEMPLATE_MAPPING, client=httpx.Client(transport=transport))


def test_request_endpoint_headers_and_template_mapping():
    captured = {}
    def handler(request):
        captured["request"] = request
        return httpx.Response(200, json={"messages": [{"id": "wamid.test-1"}]})
    result = provider(handler).send(message())
    request = captured["request"]
    body = request.read()
    assert str(request.url) == "https://graph.facebook.com/v99.0/test-phone-number-id/messages"
    assert request.headers["Authorization"] == f"Bearer {TOKEN}"
    assert request.headers["Content-Type"] == "application/json"
    assert b"messaging_product" in body and b"recipient_type" in body and b"template" in body
    import json
    template = json.loads(body)["template"]
    assert template["components"][0] == {"type": "body", "parameters": [
        {"type": "text", "text": "2026-09-23T10:00:00+00:00"},
        {"type": "text", "text": "Profesional de prueba"},
    ]}
    buttons = template["components"][1:]
    # Meta template URLs: confirmar?token={{1}} (button 0), cancelar?token={{1}} (button 1).
    # Cloud API receives only the value substituted for {{1}}: the signed token.
    assert [(button["sub_type"], button["index"], button["parameters"][0]["text"]) for button in buttons] == [
        ("url", "0", "fake-confirm-token"), ("url", "1", "fake-cancel-token"),
    ]
    assert all("https://" not in button["parameters"][0]["text"] for button in buttons)
    assert result.accepted and result.provider_message_id == "wamid.test-1"


@pytest.mark.parametrize("status", [400, 401, 403, 429, 500])
def test_http_errors_are_sanitized(status):
    def handler(request):
        return httpx.Response(status, json={"error": {"code": 190, "message": TOKEN, "type": "OAuthException"}})
    with pytest.raises(MessagingProviderError) as error:
        provider(handler).send(message())
    assert TOKEN not in str(error.value)
    assert "190" in str(error.value)


def test_invalid_success_and_non_json_fail_without_body_or_token():
    for response in (httpx.Response(200, json={}), httpx.Response(200, json={"messages": [{}]}), httpx.Response(500, text=f"Authorization Bearer {TOKEN}")):
        with pytest.raises(MessagingProviderError) as error:
            provider(lambda request, response=response: response).send(message())
        assert TOKEN not in str(error.value)


def test_unknown_message_type_and_invalid_recipient_fail():
    with pytest.raises(MessagingProviderError): provider(lambda request: httpx.Response(200, json={"messages": [{"id": "x"}]})).send(message("unknown"))
    with pytest.raises(MessagingProviderError): provider(lambda request: httpx.Response(200, json={"messages": [{"id": "x"}]})).send(OutboundMessage(channel="whatsapp", recipient="+549", message_type="appointment_reminder_v1"))


def test_timeout_is_sanitized():
    def handler(request): raise httpx.ReadTimeout("secret transport detail", request=request)
    with pytest.raises(MessagingProviderError) as error: provider(handler).send(message())
    assert TOKEN not in str(error.value)


def test_factory_keeps_fake_and_builds_meta_or_rejects_incomplete_config():
    assert isinstance(get_messaging_provider("fake"), FakeMessagingProvider)
    assert isinstance(get_messaging_provider("meta", api_version="v99.0", phone_number_id="test-id", access_token=SecretStr(TOKEN)), MetaWhatsAppProvider)
    with pytest.raises(MessagingConfigurationError): get_messaging_provider("meta", api_version="v99.0", phone_number_id="", access_token=None)


def test_default_template_mapping_includes_appointment_reminder():
    mapping = DEFAULT_TEMPLATE_MAPPING["appointment_reminder_v1"]

    assert mapping.name == "appointment_reminder_v1"
    assert mapping.language_code == "es_AR"
    assert mapping.body_parameter_keys == ("appointment_datetime", "professional_name")
    assert mapping.button_parameter_keys == ("confirm_token", "cancel_token")
    provider = get_messaging_provider(
        "meta", api_version="v99.0", phone_number_id="test-id", access_token=SecretStr(TOKEN),
    )
    assert "appointment_reminder_v1" in provider._template_mapping
    provider.close()
    customized = get_messaging_provider(
        "meta",
        api_version="v99.0",
        phone_number_id="test-id",
        access_token=SecretStr(TOKEN),
        template_mapping=TEMPLATE_MAPPING,
    )
    assert customized._template_mapping == TEMPLATE_MAPPING
    customized.close()
