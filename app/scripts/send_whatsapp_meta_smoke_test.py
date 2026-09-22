"""Manual, opt-in smoke test for the Meta WhatsApp provider.

Exit codes: 0 valid dry-run or accepted send, 1 invalid configuration,
2 invalid arguments, 3 provider/send error.
"""

import argparse
import os
import sys

from app.integrations.messaging import MetaTemplateDefinition, MessagingProviderError, OutboundMessage
from app.integrations.messaging.meta_whatsapp import MetaWhatsAppProvider


SMOKE_TEMPLATE = {
    "meta_smoke_test": MetaTemplateDefinition(name="hello_world", language_code="en_US")
}


def _masked(value: str) -> str:
    return "*" * max(0, len(value) - 4) + value[-4:]


def _recipient(value: str) -> str:
    if not value.isdigit() or not 8 <= len(value) <= 15:
        raise ValueError("El recipient debe ser un número internacional de 8 a 15 dígitos.")
    return value


def _validate_configuration() -> tuple[str, str, str] | None:
    enabled = os.getenv("WHATSAPP_ENABLED", "").strip().lower()
    provider = os.getenv("WHATSAPP_PROVIDER", "").strip().lower()
    api_version = os.getenv("WHATSAPP_API_VERSION", "").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    if enabled != "true":
        print("Configuración inválida: WHATSAPP_ENABLED debe ser true.", file=sys.stderr)
        return None
    if provider != "meta":
        print("Configuración inválida: WHATSAPP_PROVIDER debe ser meta.", file=sys.stderr)
        return None
    values = api_version, phone_number_id, token
    if not all(values):
        print("Configuración inválida: faltan variables Meta de WhatsApp.", file=sys.stderr)
        return None
    return values


def _provider(api_version: str, phone_number_id: str, token: str) -> MetaWhatsAppProvider:
    return MetaWhatsAppProvider(
        api_version=api_version,
        phone_number_id=phone_number_id,
        access_token=token,
        template_mapping=SMOKE_TEMPLATE,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke test manual y explícito de WhatsApp Meta.")
    parser.add_argument("--recipient", required=True, help="Número internacional ya normalizado, sólo dígitos.")
    parser.add_argument("--send", action="store_true", help="Confirma el único envío real.")
    args = parser.parse_args(argv)
    try:
        recipient = _recipient(args.recipient)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    configuration = _validate_configuration()
    if configuration is None:
        return 1
    api_version, phone_number_id, token = configuration
    message = OutboundMessage(channel="whatsapp", recipient=recipient, message_type="meta_smoke_test", payload={}, metadata={})
    if not args.send:
        print("Provider: meta")
        print("Template: hello_world")
        print("Language: en_US")
        print(f"Recipient: {_masked(recipient)}")
        print("Endpoint configured: yes")
        print("Access token configured: yes")
        print("SEND: disabled")
        return 0
    provider = None
    try:
        provider = _provider(api_version, phone_number_id, token)
        result = provider.send(message)
        print("WhatsApp smoke test accepted.")
        print(f"Provider message id: {result.provider_message_id}")
        return 0
    except MessagingProviderError as error:
        safe_error = str(error).replace(token, "[REDACTED]").replace("Authorization", "[REDACTED]")
        print(f"WhatsApp smoke test failed: {safe_error}", file=sys.stderr)
        return 3
    finally:
        if provider is not None:
            provider.close()


if __name__ == "__main__":
    raise SystemExit(main())
