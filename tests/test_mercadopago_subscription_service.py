import httpx
import pytest

from app.core.config import Settings
from app.services.mercadopago_subscription_service import (
    MercadoPagoSubscriptionConfigurationError,
    MercadoPagoSubscriptionError,
    MercadoPagoSubscriptionService,
)


def crear_gateway(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return MercadoPagoSubscriptionService("token-secreto", client=client)


@pytest.mark.parametrize(
    ("invocacion", "method", "path", "body"),
    [
        (lambda servicio: servicio.crear_plan({"reason": "Plan"}), "POST", "/preapproval_plan", {"reason": "Plan"}),
        (lambda servicio: servicio.consultar_plan("plan-1"), "GET", "/preapproval_plan/plan-1", None),
        (lambda servicio: servicio.crear_preapproval({"reason": "Alta"}, idempotency_key="key-1"), "POST", "/preapproval", {"reason": "Alta"}),
        (lambda servicio: servicio.consultar_preapproval("pre-1"), "GET", "/preapproval/pre-1", None),
        (lambda servicio: servicio.cancelar_preapproval("pre-1"), "PUT", "/preapproval/pre-1", {"status": "canceled"}),
        (lambda servicio: servicio.consultar_authorized_payment("pay-1"), "GET", "/authorized_payments/pay-1", None),
    ],
)
def test_operaciones_gateway(invocacion, method, path, body):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == method
        assert request.url.path == path
        assert request.headers["Authorization"] == "Bearer token-secreto"
        if path == "/preapproval":
            assert request.headers["X-Idempotency-Key"] == "key-1"
        if body is not None:
            import json

            assert json.loads(request.content) == body
        return httpx.Response(200, json={"id": "resultado"})

    servicio = crear_gateway(handler)
    assert invocacion(servicio) == {"id": "resultado"}
    servicio.close()


def test_rechaza_token_vacio():
    with pytest.raises(MercadoPagoSubscriptionConfigurationError):
        MercadoPagoSubscriptionService("  ")


def test_preapproval_no_envia_x_scope_y_usa_idempotencia():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/preapproval"
        assert request.headers["X-Idempotency-Key"] == "key-1"
        assert "x-scope" not in request.headers
        return httpx.Response(200, json={"id": "pre-1"})

    servicio = crear_gateway(handler)
    assert servicio.crear_preapproval({"status": "authorized"}, idempotency_key="key-1") == {"id": "pre-1"}
    servicio.close()


def test_buscar_preapprovals_por_referencia():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/preapproval/search"
        assert request.url.params["q"] == "referencia-1"
        return httpx.Response(200, json={"results": [{"id": "pre-1"}]})

    servicio = crear_gateway(handler)
    assert servicio.buscar_preapprovals("referencia-1") == [{"id": "pre-1"}]
    servicio.close()


def test_error_http_es_sanitizado():
    secreto_remoto = "detalle-privado-del-proveedor"

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={
            "message": secreto_remoto,
            "error": "bad_request",
            "cause": [{"code": "invalid_parameter"}],
            "authorization": "Bearer no-debe-aparecer",
        })

    servicio = crear_gateway(handler)
    with pytest.raises(MercadoPagoSubscriptionError) as captura:
        servicio.consultar_plan("plan-1")

    assert captura.value.status_code == 401
    assert captura.value.operation == "consultar_plan"
    assert secreto_remoto not in str(captura.value)
    assert captura.value.provider_response == {
        "message": secreto_remoto,
        "error": "bad_request",
        "cause": [{"code": "invalid_parameter"}],
        "authorization": "[REDACTED]",
    }
    assert "no-debe-aparecer" not in repr(captura.value.provider_response)


def test_timeout_es_sanitizado():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("incluye secreto", request=request)

    servicio = crear_gateway(handler)
    with pytest.raises(MercadoPagoSubscriptionError) as captura:
        servicio.consultar_preapproval("pre-1")

    assert captura.value.status_code is None
    assert "secreto" not in str(captura.value)


def test_respuesta_no_json_es_rechazada():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="respuesta inesperada")

    servicio = crear_gateway(handler)
    with pytest.raises(MercadoPagoSubscriptionError):
        servicio.consultar_authorized_payment("pay-1")


def test_id_de_recurso_se_codifica_en_la_url():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.raw_path == b"/preapproval_plan/plan%2Fcon%20barra"
        return httpx.Response(200, json={})

    servicio = crear_gateway(handler)
    assert servicio.consultar_plan("plan/con barra") == {}


def test_settings_carga_configuracion_saas_separada():
    configuracion = Settings(
        _env_file=None,
        jwt_secret_key="test-secret",
        mercado_pago_access_token="token-clinico",
        mercado_pago_webhook_secret="webhook-clinico",
        mercadopago_access_token="APP_USR-fake-access-token",
        mercadopago_public_key="APP_USR-fake-public-key",
        mercadopago_env="production",
        mercadopago_webhook_secret="webhook-saas",
    )

    assert configuracion.mercado_pago_access_token == "token-clinico"
    assert configuracion.mercadopago_access_token is not None
    assert (
        configuracion.mercadopago_access_token.get_secret_value()
        == "APP_USR-fake-access-token"
    )
    assert configuracion.mercadopago_public_key == "APP_USR-fake-public-key"
    assert configuracion.mercadopago_env == "production"
    assert configuracion.mercadopago_webhook_secret is not None


def test_settings_acepta_token_app_usr_en_produccion():
    configuracion = Settings(
        _env_file=None,
        jwt_secret_key="test-secret",
        mercadopago_env="production",
        mercadopago_access_token="APP_USR-fake-access-token",
        mercadopago_public_key="APP_USR-fake-public-key",
    )
    assert configuracion.mercadopago_env == "production"


def test_settings_rechaza_token_test_en_produccion():
    with pytest.raises(ValueError, match="APP_USR"):
        Settings(
            _env_file=None,
            jwt_secret_key="test-secret",
            mercadopago_env="production",
            mercadopago_access_token="TEST-fake-access-token",
            mercadopago_public_key="APP_USR-fake-public-key",
        )


def test_settings_acepta_token_test_en_sandbox():
    configuracion = Settings(
        _env_file=None,
        jwt_secret_key="test-secret",
        mercadopago_env="sandbox",
        mercadopago_access_token="TEST-fake-access-token",
        mercadopago_public_key="APP_USR-fake-public-key",
    )
    assert configuracion.mercadopago_env == "sandbox"


def test_settings_rechaza_token_app_usr_en_sandbox():
    with pytest.raises(ValueError, match="TEST"):
        Settings(
            _env_file=None,
            jwt_secret_key="test-secret",
            mercadopago_env="sandbox",
            mercadopago_access_token="APP_USR-fake-access-token",
            mercadopago_public_key="APP_USR-fake-public-key",
        )


def test_settings_rechaza_entorno_mercadopago_invalido():
    with pytest.raises(ValueError):
        Settings(_env_file=None, jwt_secret_key="test-secret", mercadopago_env="qa")


def test_settings_requiere_public_key_si_mercadopago_esta_configurado():
    with pytest.raises(ValueError, match="MERCADOPAGO_PUBLIC_KEY"):
        Settings(
            _env_file=None,
            jwt_secret_key="test-secret",
            mercadopago_access_token="APP_USR-fake-access-token",
            mercadopago_public_key="",
        )


def test_settings_requiere_access_token_si_public_key_esta_configurada():
    with pytest.raises(ValueError, match="MERCADOPAGO_ACCESS_TOKEN"):
        Settings(
            _env_file=None,
            jwt_secret_key="test-secret",
            mercadopago_public_key="APP_USR-fake-public-key",
        )
