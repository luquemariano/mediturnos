from collections.abc import Mapping
import re
from typing import Any
from urllib.parse import quote

import httpx


MERCADOPAGO_API_BASE_URL = "https://api.mercadopago.com"
MERCADOPAGO_TIMEOUT_SECONDS = 10.0


class MercadoPagoSubscriptionError(RuntimeError):
    """Error sanitizado al comunicarse con Mercado Pago Suscripciones."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        operation: str | None = None,
        provider_response: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.operation = operation
        self.provider_response = provider_response


class MercadoPagoSubscriptionConfigurationError(
    MercadoPagoSubscriptionError
):
    """La integración no tiene las credenciales mínimas para operar."""


class MercadoPagoSubscriptionService:
    """Gateway HTTP aislado para la API de Suscripciones de Mercado Pago."""

    def __init__(
        self,
        access_token: str,
        *,
        client: httpx.Client | None = None,
        base_url: str = MERCADOPAGO_API_BASE_URL,
        timeout_seconds: float = MERCADOPAGO_TIMEOUT_SECONDS,
    ) -> None:
        token = access_token.strip()
        if not token:
            raise MercadoPagoSubscriptionConfigurationError(
                "MERCADOPAGO_ACCESS_TOKEN es obligatorio."
            )
        if timeout_seconds <= 0:
            raise MercadoPagoSubscriptionConfigurationError(
                "El timeout de Mercado Pago debe ser mayor que cero."
            )

        self._client = client or httpx.Client()
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds)
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def crear_plan(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST", "/preapproval_plan", operation="crear_plan", json=payload
        )

    def consultar_plan(self, plan_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/preapproval_plan/{self._required_id(plan_id)}",
            operation="consultar_plan",
        )

    def crear_preapproval(
        self,
        payload: Mapping[str, Any],
        *,
        idempotency_key: str,
    ) -> dict[str, Any]:
        key = idempotency_key.strip()
        if not key:
            raise MercadoPagoSubscriptionConfigurationError(
                "La clave de idempotencia es obligatoria."
            )
        return self._request(
            "POST",
            "/preapproval",
            operation="crear_preapproval",
            json=payload,
            extra_headers={"X-Idempotency-Key": key},
        )

    def consultar_preapproval(self, preapproval_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/preapproval/{self._required_id(preapproval_id)}",
            operation="consultar_preapproval",
        )

    def buscar_preapprovals(
        self, external_reference: str
    ) -> list[dict[str, Any]]:
        referencia = external_reference.strip()
        if not referencia:
            raise MercadoPagoSubscriptionConfigurationError(
                "La referencia externa es obligatoria."
            )
        data = self._request(
            "GET",
            "/preapproval/search",
            operation="buscar_preapprovals",
            params={"q": referencia},
        )
        results = data.get("results")
        if not isinstance(results, list) or not all(
            isinstance(item, dict) for item in results
        ):
            raise MercadoPagoSubscriptionError(
                "Mercado Pago devolvió una búsqueda inválida.",
                operation="buscar_preapprovals",
            )
        return results

    def cancelar_preapproval(self, preapproval_id: str) -> dict[str, Any]:
        return self._request(
            "PUT",
            f"/preapproval/{self._required_id(preapproval_id)}",
            operation="cancelar_preapproval",
            json={"status": "canceled"},
        )

    def consultar_authorized_payment(
        self, authorized_payment_id: str
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/authorized_payments/{self._required_id(authorized_payment_id)}",
            operation="consultar_authorized_payment",
        )

    def consultar_payment(self, payment_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/v1/payments/{self._required_id(payment_id)}",
            operation="consultar_payment",
        )

    def close(self) -> None:
        self._client.close()

    @staticmethod
    def _required_id(resource_id: str) -> str:
        normalized_id = resource_id.strip()
        if not normalized_id:
            raise MercadoPagoSubscriptionConfigurationError(
                "El identificador del recurso de Mercado Pago es inválido."
            )
        return quote(normalized_id, safe="")

    def _request(
        self,
        method: str,
        path: str,
        *,
        operation: str,
        json: Mapping[str, Any] | None = None,
        extra_headers: Mapping[str, str] | None = None,
        params: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        headers = dict(self._headers)
        if extra_headers is not None:
            headers.update(extra_headers)
        try:
            response = self._client.request(
                method,
                f"{self._base_url}{path}",
                headers=headers,
                json=dict(json) if json is not None else None,
                params=dict(params) if params is not None else None,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException as error:
            raise MercadoPagoSubscriptionError(
                "Mercado Pago no respondió dentro del tiempo esperado.",
                operation=operation,
            ) from error
        except httpx.HTTPStatusError as error:
            raise MercadoPagoSubscriptionError(
                "Mercado Pago rechazó la operación solicitada.",
                status_code=error.response.status_code,
                operation=operation,
                provider_response=self._safe_error_response(error.response),
            ) from error
        except httpx.RequestError as error:
            raise MercadoPagoSubscriptionError(
                "No fue posible comunicarse con Mercado Pago.",
                operation=operation,
            ) from error

        try:
            data = response.json()
        except ValueError as error:
            raise MercadoPagoSubscriptionError(
                "Mercado Pago devolvió una respuesta inválida.",
                status_code=response.status_code,
                operation=operation,
            ) from error

        if not isinstance(data, dict):
            raise MercadoPagoSubscriptionError(
                "Mercado Pago devolvió una respuesta inválida.",
                status_code=response.status_code,
                operation=operation,
            )
        return data

    @classmethod
    def _safe_error_response(cls, response: httpx.Response) -> Any:
        try:
            body: Any = response.json()
        except ValueError:
            return "[respuesta no JSON omitida]"
        return cls._redact_sensitive(body)

    @classmethod
    def _redact_sensitive(cls, value: Any) -> Any:
        sensitive_keys = {
            "access_token",
            "authorization",
            "card_token_id",
            "card_number",
            "cvv",
            "number",
            "public_key",
            "security_code",
            "token",
        }
        if isinstance(value, dict):
            return {
                key: "[REDACTED]"
                if key.lower() in sensitive_keys
                else cls._redact_sensitive(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [cls._redact_sensitive(item) for item in value]
        if isinstance(value, str):
            value = re.sub(r"Bearer\s+\S+", "Bearer [REDACTED]", value, flags=re.IGNORECASE)
            value = re.sub(r"\b(?:APP_USR|TEST)-\S+", "[REDACTED]", value)
            value = re.sub(r"\b\d{12,19}\b", "[REDACTED]", value)
        return value
