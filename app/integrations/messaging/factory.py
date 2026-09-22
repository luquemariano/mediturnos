from .base import MessagingConfigurationError, MessagingProvider
from .fake import FakeMessagingProvider
from .meta_whatsapp import MetaWhatsAppProvider


def get_messaging_provider(provider: str, **config) -> MessagingProvider:
    if provider == "fake":
        return FakeMessagingProvider()
    if provider == "meta":
        required = ("api_version", "phone_number_id", "access_token")
        if any(not config.get(key) for key in required):
            raise MessagingConfigurationError("El provider Meta de WhatsApp requiere configuración completa.")
        return MetaWhatsAppProvider(
            api_version=config["api_version"],
            phone_number_id=config["phone_number_id"],
            access_token=config["access_token"],
            template_mapping=config.get("template_mapping"),
        )
    raise MessagingConfigurationError("El proveedor de mensajería solicitado no está disponible.")
