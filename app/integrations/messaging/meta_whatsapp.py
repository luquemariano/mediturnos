from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import SecretStr

from .base import MessageDeliveryResult, MessagingProviderError, OutboundMessage


META_GRAPH_BASE_URL = "https://graph.facebook.com"
META_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class MetaTemplateDefinition:
    name: str
    language_code: str
    body_parameter_keys: tuple[str, ...] = ()
    button_parameter_keys: tuple[str, ...] = ()


DEFAULT_TEMPLATE_MAPPING = {
    "appointment_reminder_v1": MetaTemplateDefinition(
        name="appointment_reminder_v1",
        language_code="es_AR",
        body_parameter_keys=("appointment_datetime", "professional_name"),
        button_parameter_keys=("confirm_token", "cancel_token"),
    ),
}


class MetaWhatsAppProvider:
    def __init__(
        self,
        *,
        api_version: str,
        phone_number_id: str,
        access_token: str | SecretStr,
        template_mapping: Mapping[str, MetaTemplateDefinition] | None = None,
        client: httpx.Client | None = None,
        timeout_seconds: float = META_TIMEOUT_SECONDS,
    ) -> None:
        self._api_version = self._required(api_version, "api_version")
        self._phone_number_id = self._required(phone_number_id, "phone_number_id")
        if timeout_seconds <= 0:
            raise ValueError("El timeout de WhatsApp debe ser mayor que cero.")
        token = access_token.get_secret_value() if isinstance(access_token, SecretStr) else access_token
        self._access_token = self._required(token, "access_token")
        self._owns_client = client is None
        self._client = client or httpx.Client()
        self._timeout = httpx.Timeout(timeout_seconds)
        self._template_mapping = dict(
            DEFAULT_TEMPLATE_MAPPING if template_mapping is None else template_mapping
        )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    @staticmethod
    def _required(value: str, name: str) -> str:
        value = (value or "").strip()
        if not value:
            raise ValueError(f"{name} es obligatorio.")
        return value

    def send(self, message: OutboundMessage) -> MessageDeliveryResult:
        if message.channel != "whatsapp":
            raise MessagingProviderError("Meta WhatsApp sólo admite mensajes WhatsApp.")
        if not isinstance(message.recipient, str) or not message.recipient.isdigit():
            raise MessagingProviderError("El destinatario de WhatsApp no es válido.")
        definition = self._template_mapping.get(message.message_type)
        if definition is None:
            raise MessagingProviderError("El tipo de template de WhatsApp no está configurado.")
        body = self._template_body(message, definition)
        url = f"{META_GRAPH_BASE_URL}/{self._api_version}/{self._phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }
        try:
            response = self._client.post(
                url,
                headers=headers,
                json=body,
                timeout=self._timeout,
            )
        except httpx.TimeoutException as error:
            raise MessagingProviderError("WhatsApp no respondió dentro del tiempo esperado.") from error
        except httpx.RequestError as error:
            raise MessagingProviderError("No fue posible comunicarse con WhatsApp.") from error

        if response.status_code < 200 or response.status_code >= 300:
            raise MessagingProviderError(self._http_error(response))
        try:
            data = response.json()
        except ValueError as error:
            raise MessagingProviderError("WhatsApp devolvió una respuesta no válida.") from error
        try:
            message_id = data["messages"][0]["id"]
        except (KeyError, IndexError, TypeError) as error:
            raise MessagingProviderError("WhatsApp devolvió una respuesta sin ID de mensaje.") from error
        if not isinstance(message_id, str) or not message_id.strip():
            raise MessagingProviderError("WhatsApp devolvió un ID de mensaje inválido.")
        return MessageDeliveryResult(accepted=True, provider="meta_whatsapp", provider_message_id=message_id)

    @staticmethod
    def _template_body(message: OutboundMessage, definition: MetaTemplateDefinition) -> dict[str, Any]:
        payload = message.payload
        parameters = [{"type": "text", "text": str(payload[key])} for key in definition.body_parameter_keys if key in payload]
        components: list[dict[str, Any]] = []
        if parameters:
            components.append({"type": "body", "parameters": parameters})
        for index, key in enumerate(definition.button_parameter_keys):
            if key in payload:
                components.append({"type": "button", "sub_type": "url", "index": str(index), "parameters": [{"type": "text", "text": str(payload[key])}]})
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": message.recipient,
            "type": "template",
            "template": {"name": definition.name, "language": {"code": definition.language_code}, "components": components},
        }

    @staticmethod
    def _http_error(response: httpx.Response) -> str:
        try:
            data = response.json()
            error = data.get("error", {}) if isinstance(data, dict) else {}
            if isinstance(error, dict):
                code = error.get("code")
                subcode = error.get("error_subcode")
                error_type = error.get("type")
                details = ", ".join(str(value) for value in (code, subcode, error_type) if value is not None)
                if details:
                    return f"WhatsApp rechazó el mensaje (HTTP {response.status_code}; {details})."
        except ValueError:
            pass
        return f"WhatsApp rechazó el mensaje (HTTP {response.status_code})."
