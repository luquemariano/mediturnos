from .base import MessagingConfigurationError, MessagingProvider
from .fake import FakeMessagingProvider


def get_messaging_provider(provider: str) -> MessagingProvider:
    if provider == "fake":
        return FakeMessagingProvider()
    raise MessagingConfigurationError("El proveedor de mensajería solicitado no está disponible.")
