import pytest

from app.integrations.messaging import (
    FakeMessagingProvider,
    MessageDeliveryResult,
    MessagingConfigurationError,
    MessagingProvider,
    MessagingProviderError,
    OutboundMessage,
    get_messaging_provider,
)


def mensaje():
    return OutboundMessage(
        channel="whatsapp",
        recipient="5493515551234",
        message_type="appointment_reminder",
        payload={"template": "reminder"},
        metadata={"source": "test"},
    )


def test_fake_acepta_y_registra_mensaje_en_memoria():
    provider = FakeMessagingProvider()

    resultado = provider.send(mensaje())

    assert isinstance(provider, MessagingProvider)
    assert isinstance(resultado, MessageDeliveryResult)
    assert resultado.accepted is True
    assert resultado.provider == "fake"
    assert resultado.provider_message_id == "fake-message-000001"
    assert provider.sent_messages == [mensaje()]


def test_fake_genera_ids_diferenciables_y_no_hace_io_externo():
    provider = FakeMessagingProvider()

    primero = provider.send(mensaje())
    segundo = provider.send(mensaje())

    assert primero.provider_message_id != segundo.provider_message_id
    assert [item.recipient for item in provider.sent_messages] == [
        "5493515551234",
        "5493515551234",
    ]


def test_factory_devuelve_fake_y_rechaza_provider_desconocido():
    assert isinstance(get_messaging_provider("fake"), FakeMessagingProvider)
    with pytest.raises(MessagingConfigurationError):
        get_messaging_provider("unknown")


def test_fake_error_controlado_no_expone_payload():
    provider = FakeMessagingProvider(fail_next=True)

    with pytest.raises(MessagingProviderError) as error:
        provider.send(mensaje())

    assert "reminder" not in str(error.value)
    assert "5493515551234" not in str(error.value)
    assert provider.sent_messages == []
