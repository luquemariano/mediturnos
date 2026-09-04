from datetime import timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from mercadopago.webhook import InvalidWebhookSignatureError, SignatureFailureReason
from pydantic import SecretStr

from app.core.datetime_utils import ahora_utc
from app.models.cobro_suscripcion import CobroSuscripcion
from app.models.cuenta import Cuenta
from app.models.cuenta_usuario import CuentaUsuario
from app.models.mercadopago_plan_suscripcion import MercadoPagoPlanSuscripcion
from app.models.notificacion_mercadopago_suscripcion import NotificacionMercadoPagoSuscripcion
from app.models.suscripcion import Suscripcion
from app.models.usuario import Usuario
from app.schemas.suscripcion import IniciarSuscripcionEntrada
from app.services import suscripcion_mercadopago_service as servicio
from app.routers import suscripciones as router_suscripciones
from tests.conftest import SessionTest

CARD_TOKEN = "card-token-efimero-sandbox"


class GatewayFalso:
    def __init__(self):
        self.payload = None
        self.idempotency_keys = []
        self.resultados_busqueda = []
        self.error_creacion = None
        self.preapproval = {
            "id": "preapproval-1", "status": "authorized", "version": 1,
            "init_point": "https://mercadopago.test/checkout",
        }
        self.cobro = {
            "id": "authorized-1", "preapproval_id": "preapproval-1",
            "status": "approved", "amount": 34900, "currency": "ARS",
        }

    def crear_preapproval(self, payload, *, idempotency_key):
        self.payload = payload
        self.idempotency_keys.append(idempotency_key)
        if self.error_creacion is not None:
            raise self.error_creacion
        return self.preapproval

    def buscar_preapprovals(self, _external_reference):
        return self.resultados_busqueda

    def consultar_preapproval(self, _resource_id):
        return self.preapproval

    def cancelar_preapproval(self, _resource_id):
        return {**self.preapproval, "status": "canceled", "version": 2}

    def consultar_authorized_payment(self, _resource_id):
        return self.cobro

    def consultar_payment(self, _resource_id):
        return self.cobro

    def consultar_plan(self, _resource_id):
        return {"id": _resource_id}


@pytest.fixture
def escenario(monkeypatch):
    db = SessionTest()
    propietario = Usuario(nombre="Propietario", email="owner@test.com", password_hash="x", rol="profesional")
    miembro = Usuario(nombre="Miembro", email="member@test.com", password_hash="x", rol="recepcionista")
    ajeno = Usuario(nombre="Ajeno", email="other@test.com", password_hash="x", rol="profesional")
    inicio = ahora_utc()
    cuenta = Cuenta(nombre="Consulta", tipo="individual", suscripcion=Suscripcion(
        plan_code="profesional", status="trial", trial_started_at=inicio,
        trial_ends_at=inicio + timedelta(days=14),
    ))
    cuenta.membresias.extend([
        CuentaUsuario(usuario=propietario, rol_cuenta="propietario"),
        CuentaUsuario(usuario=miembro, rol_cuenta="miembro"),
    ])
    plan = MercadoPagoPlanSuscripcion(
        plan_code="profesional", environment="sandbox", mp_preapproval_plan_id="plan-1",
        amount=Decimal("34900.00"), currency="ARS",
    )
    db.add_all([cuenta, ajeno, plan]); db.commit()
    gateway = GatewayFalso()
    monkeypatch.setattr(servicio, "_gateway", lambda: gateway)
    monkeypatch.setattr(
        servicio.settings,
        "mercadopago_test_payer_email",
        "buyer-test-user@testuser.com",
    )
    yield db, cuenta, propietario, miembro, ajeno, gateway
    db.close()


def test_iniciar_sandbox_omite_inicio_sin_free_trial_y_no_activa_authorized(
    escenario, caplog
):
    db, cuenta, propietario, _, _, gateway = escenario
    respuesta = servicio.iniciar_suscripcion(
        db, cuenta.id, propietario, "profesional", CARD_TOKEN
    )
    db.refresh(cuenta.suscripcion)
    assert respuesta.estado == "trial"
    assert gateway.payload["card_token_id"] == CARD_TOKEN
    assert gateway.payload["status"] == "authorized"
    assert gateway.payload["auto_recurring"]["frequency"] == 1
    assert gateway.payload["auto_recurring"]["frequency_type"] == "months"
    assert gateway.payload["auto_recurring"]["transaction_amount"] == 34900.0
    assert gateway.payload["auto_recurring"]["currency_id"] == "ARS"
    assert "start_date" not in gateway.payload["auto_recurring"]
    assert "free_trial" not in gateway.payload
    assert cuenta.suscripcion.billing_amount == Decimal("34900.00")
    assert cuenta.suscripcion.status == "trial"
    assert len(gateway.idempotency_keys) == 1
    assert cuenta.suscripcion.mp_preapproval_id == "preapproval-1"
    assert cuenta.suscripcion.mp_idempotency_key is None
    assert "mp_idempotency_key" not in respuesta.model_dump()
    assert CARD_TOKEN not in repr(vars(cuenta.suscripcion))
    assert CARD_TOKEN not in caplog.text


@pytest.mark.parametrize(
    ("plan_code", "precio"),
    [
        ("profesional", Decimal("34900.00")),
        ("consultorio", Decimal("69900.00")),
        ("centro", Decimal("149900.00")),
    ],
)
def test_iniciar_usa_catalogo_backend_para_importes_y_recurrencia(
    escenario, plan_code, precio
):
    db, cuenta, propietario, _, _, gateway = escenario
    if plan_code != "profesional":
        db.add(MercadoPagoPlanSuscripcion(
            plan_code=plan_code,
            environment="sandbox",
            mp_preapproval_plan_id=f"plan-{plan_code}",
            amount=precio,
            currency="ARS",
        ))
        db.commit()

    servicio.iniciar_suscripcion(
        db, cuenta.id, propietario, plan_code, CARD_TOKEN
    )

    recurrencia = gateway.payload["auto_recurring"]
    assert recurrencia == {
        "frequency": 1,
        "frequency_type": "months",
        "transaction_amount": float(precio),
        "currency_id": "ARS",
    }
    assert "free_trial" not in gateway.payload


def test_contrato_inicio_no_acepta_importe_del_frontend():
    assert set(IniciarSuscripcionEntrada.model_fields) == {"plan", "card_token_id"}


def test_sandbox_usa_email_del_buyer_test_user(escenario):
    db, cuenta, propietario, _, _, gateway = escenario

    servicio.iniciar_suscripcion(
        db, cuenta.id, propietario, "profesional", CARD_TOKEN
    )

    assert gateway.payload["payer_email"] == "buyer-test-user@testuser.com"
    assert gateway.payload["payer_email"] != propietario.email


def test_produccion_usa_email_del_usuario_de_turnelia(escenario, monkeypatch):
    db, cuenta, propietario, _, _, gateway = escenario
    plan = db.query(MercadoPagoPlanSuscripcion).filter_by(
        plan_code="profesional"
    ).one()
    plan.environment = "production"
    db.commit()
    monkeypatch.setattr(servicio.settings, "mercadopago_env", "production")
    servicio.iniciar_suscripcion(
        db, cuenta.id, propietario, "profesional", CARD_TOKEN
    )

    assert gateway.payload["payer_email"] == propietario.email
    assert gateway.payload["auto_recurring"] == {
        "frequency": 1,
        "frequency_type": "months",
        "transaction_amount": 34900.0,
        "currency_id": "ARS",
    }
    assert gateway.payload["preapproval_plan_id"] == "plan-1"
    assert gateway.payload["card_token_id"] == CARD_TOKEN
    assert gateway.payload["status"] == "authorized"
    assert gateway.payload["back_url"].endswith("/suscripcion/retorno")
    assert gateway.payload["external_reference"]
    assert "free_trial" not in gateway.payload


def test_sandbox_sin_buyer_email_falla_antes_del_gateway(
    escenario, monkeypatch
):
    db, cuenta, propietario, _, _, gateway = escenario
    monkeypatch.setattr(servicio.settings, "mercadopago_test_payer_email", None)
    gateway_invocado = False

    def gateway_inesperado():
        nonlocal gateway_invocado
        gateway_invocado = True
        return gateway

    monkeypatch.setattr(servicio, "_gateway", gateway_inesperado)

    with pytest.raises(HTTPException) as error:
        servicio.iniciar_suscripcion(
            db, cuenta.id, propietario, "profesional", CARD_TOKEN
        )

    assert error.value.status_code == 503
    assert error.value.detail == "Falta configurar el comprador de prueba de Mercado Pago."
    assert gateway_invocado is False
    db.refresh(cuenta.suscripcion)
    assert cuenta.suscripcion.mp_idempotency_key is None
    assert cuenta.suscripcion.external_reference is None


def test_frontend_no_controla_payer_email():
    assert "payer_email" not in IniciarSuscripcionEntrada.model_fields


def test_timeout_conserva_clave_y_retry_reutiliza_el_mismo_intento(escenario):
    db, cuenta, propietario, _, _, gateway = escenario
    gateway.error_creacion = servicio.MercadoPagoSubscriptionError("timeout")

    with pytest.raises(HTTPException) as error:
        servicio.iniciar_suscripcion(
            db, cuenta.id, propietario, "profesional", CARD_TOKEN
        )
    assert error.value.status_code == 502
    db.refresh(cuenta.suscripcion)
    clave = cuenta.suscripcion.mp_idempotency_key
    referencia = cuenta.suscripcion.external_reference
    assert clave is not None

    gateway.error_creacion = None
    respuesta = servicio.iniciar_suscripcion(
        db, cuenta.id, propietario, "profesional", CARD_TOKEN
    )
    assert gateway.idempotency_keys == [clave, clave]
    assert gateway.payload["external_reference"] == referencia
    assert respuesta.estado == "trial"
    db.refresh(cuenta.suscripcion)
    assert cuenta.suscripcion.mp_preapproval_id == "preapproval-1"
    assert cuenta.suscripcion.mp_idempotency_key is None


def test_error_proveedor_se_loguea_sanitizado_en_todos_los_entornos(
    escenario, monkeypatch, caplog
):
    db, cuenta, propietario, _, _, gateway = escenario
    secretos = {
        "authorization": "Bearer APP_USR-secreto-no-loguear",
        "card_token_id": "token-tarjeta-super-secreto",
        "card_number": "4509953566233704",
        "cvv": "123",
        "public_key": "TEST-publica-no-loguear",
    }
    respuesta = servicio.MercadoPagoSubscriptionService._redact_sensitive({
        "message": "Invalid payer",
        "error": "unprocessable_entity",
        "cause": [{"code": "invalid_payer_email"}],
        **secretos,
    })
    gateway.error_creacion = servicio.MercadoPagoSubscriptionError(
        "Mercado Pago rechazó la operación solicitada.",
        status_code=422,
        operation="crear_preapproval",
        provider_response=respuesta,
    )

    caplog.set_level("WARNING", logger="uvicorn.error")

    monkeypatch.setattr(servicio.settings, "app_env", "development")

    with pytest.raises(HTTPException) as error:
        servicio.iniciar_suscripcion(
            db, cuenta.id, propietario, "profesional", CARD_TOKEN
        )

    assert error.value.status_code == 502
    assert error.value.detail == "No fue posible iniciar la suscripción."
    assert "422" in caplog.text
    assert "Invalid payer" in caplog.text
    assert "unprocessable_entity" in caplog.text
    assert "invalid_payer_email" in caplog.text
    assert "[REDACTED]" in caplog.text
    assert "provider_response" in caplog.text

    for secreto in (*secretos.values(), CARD_TOKEN):
        assert secreto not in caplog.text

    caplog.clear()
    monkeypatch.setattr(servicio.settings, "app_env", "production")
    servicio._registrar_error_proveedor(gateway.error_creacion)

    assert "422" in caplog.text
    assert "Invalid payer" in caplog.text
    assert "unprocessable_entity" in caplog.text
    assert "invalid_payer_email" in caplog.text
    assert "provider_response" not in caplog.text

    for secreto in (*secretos.values(), CARD_TOKEN):
        assert secreto not in caplog.text


def test_retry_reconcilia_por_referencia_antes_de_recrear(escenario):
    db, cuenta, propietario, _, _, gateway = escenario
    gateway.error_creacion = servicio.MercadoPagoSubscriptionError("timeout")
    with pytest.raises(HTTPException):
        servicio.iniciar_suscripcion(
            db, cuenta.id, propietario, "profesional", CARD_TOKEN
        )
    db.refresh(cuenta.suscripcion)
    clave = cuenta.suscripcion.mp_idempotency_key
    gateway.error_creacion = None
    gateway.resultados_busqueda = [
        {
            **gateway.preapproval,
            "external_reference": cuenta.suscripcion.external_reference,
            "preapproval_plan_id": cuenta.suscripcion.mp_preapproval_plan_id,
            "payer_email": "buyer-test-user@testuser.com",
        }
    ]

    servicio.iniciar_suscripcion(
        db, cuenta.id, propietario, "profesional", CARD_TOKEN
    )

    assert gateway.idempotency_keys == [clave]
    db.refresh(cuenta.suscripcion)
    assert cuenta.suscripcion.mp_preapproval_id == "preapproval-1"
    assert cuenta.suscripcion.mp_idempotency_key is None


def test_operaciones_distintas_reservan_claves_distintas(escenario):
    db, cuenta, propietario, _, _, gateway = escenario
    otra = Cuenta(
        nombre="Otra consulta",
        tipo="individual",
        suscripcion=Suscripcion(
            plan_code="profesional",
            status="trial",
            trial_started_at=ahora_utc(),
            trial_ends_at=ahora_utc() + timedelta(days=14),
        ),
    )
    otra.membresias.append(
        CuentaUsuario(usuario=propietario, rol_cuenta="propietario")
    )
    db.add(otra)
    db.commit()
    gateway.error_creacion = servicio.MercadoPagoSubscriptionError("timeout")

    for cuenta_id in (cuenta.id, otra.id):
        with pytest.raises(HTTPException):
            servicio.iniciar_suscripcion(
                db, cuenta_id, propietario, "profesional", CARD_TOKEN
            )

    db.refresh(cuenta.suscripcion)
    db.refresh(otra.suscripcion)
    assert cuenta.suscripcion.mp_idempotency_key is not None
    assert otra.suscripcion.mp_idempotency_key is not None
    assert (
        cuenta.suscripcion.mp_idempotency_key
        != otra.suscripcion.mp_idempotency_key
    )


def test_doble_inicio_y_roles_de_cuenta(escenario):
    db, cuenta, propietario, miembro, ajeno, _ = escenario
    with pytest.raises(HTTPException) as miembro_error:
        servicio.iniciar_suscripcion(db, cuenta.id, miembro, "profesional", CARD_TOKEN)
    assert miembro_error.value.status_code == 403
    with pytest.raises(HTTPException) as ajeno_error:
        servicio.obtener_estado_suscripcion(db, cuenta.id, ajeno)
    assert ajeno_error.value.status_code == 403
    servicio.iniciar_suscripcion(db, cuenta.id, propietario, "profesional", CARD_TOKEN)
    with pytest.raises(HTTPException) as duplicado:
        servicio.iniciar_suscripcion(db, cuenta.id, propietario, "profesional", CARD_TOKEN)
    assert duplicado.value.status_code == 409


def test_cobro_aprobado_activa_y_webhook_duplicado_es_idempotente(escenario):
    db, cuenta, propietario, _, _, _ = escenario
    servicio.iniciar_suscripcion(db, cuenta.id, propietario, "profesional", CARD_TOKEN)
    argumentos = dict(
        topic="subscription_authorized_payment", resource_id="authorized-1",
        request_id="request-1", action="created", payload={"type": "subscription_authorized_payment", "data": {"id": "authorized-1"}},
    )
    assert servicio.procesar_webhook_suscripcion(db, **argumentos) is True
    db.refresh(cuenta.suscripcion)
    assert cuenta.suscripcion.status == "active"
    assert db.query(CobroSuscripcion).count() == 1
    assert servicio.procesar_webhook_suscripcion(db, **argumentos) is False
    assert db.query(NotificacionMercadoPagoSuscripcion).count() == 1


def test_cancelacion_es_idempotente(escenario):
    db, cuenta, propietario, _, _, _ = escenario
    servicio.iniciar_suscripcion(db, cuenta.id, propietario, "profesional", CARD_TOKEN)
    primera = servicio.cancelar_suscripcion(db, cuenta.id, propietario)
    segunda = servicio.cancelar_suscripcion(db, cuenta.id, propietario)
    assert primera.suscripcion.estado == "cancelled"
    assert segunda.procesado is False


def test_evento_preapproval_antiguo_no_revierte_estado(escenario):
    db, cuenta, propietario, _, _, gateway = escenario
    servicio.iniciar_suscripcion(db, cuenta.id, propietario, "profesional", CARD_TOKEN)
    cuenta.suscripcion.mp_version = 5
    cuenta.suscripcion.status = "active"
    db.commit()
    gateway.preapproval = {"id": "preapproval-1", "status": "paused", "version": 4}
    assert servicio.procesar_webhook_suscripcion(
        db, topic="subscription_preapproval", resource_id="preapproval-1",
        request_id="request-old", action="updated", payload={"data": {"id": "preapproval-1"}},
    ) is False
    db.refresh(cuenta.suscripcion)
    assert cuenta.suscripcion.status == "active"


def test_estado_preapproval_desconocido_no_activa(escenario):
    db, cuenta, propietario, _, _, gateway = escenario
    gateway.preapproval["status"] = "future_status"
    servicio.iniciar_suscripcion(db, cuenta.id, propietario, "profesional", CARD_TOKEN)
    assert cuenta.suscripcion.status == "trial"


def test_webhook_valida_firma_e_identificador(client, monkeypatch):
    monkeypatch.setattr(router_suscripciones.settings, "mercadopago_webhook_secret", SecretStr("secret"))
    monkeypatch.setattr(
        router_suscripciones.WebhookSignatureValidator, "validate",
        lambda signature, request_id, data_id, secret: None,
    )
    llamado = {}
    monkeypatch.setattr(
        router_suscripciones, "procesar_webhook_suscripcion",
        lambda db, **kwargs: llamado.update(kwargs) or True,
    )
    respuesta = client.post(
        "/webhooks/mercadopago/suscripciones?data.id=preapproval-1",
        headers={"x-signature": "ts=1,v1=firma", "x-request-id": "req-1"},
        json={"type": "subscription_preapproval", "data": {"id": "preapproval-1"}},
    )
    assert respuesta.status_code == 200
    assert llamado["resource_id"] == "preapproval-1"
    inconsistente = client.post(
        "/webhooks/mercadopago/suscripciones?data.id=firmado",
        headers={"x-signature": "ts=1,v1=firma", "x-request-id": "req-2"},
        json={"type": "subscription_preapproval", "data": {"id": "otro"}},
    )
    assert inconsistente.status_code == 400


def test_webhook_rechaza_firma_invalida(client, monkeypatch):
    monkeypatch.setattr(router_suscripciones.settings, "mercadopago_webhook_secret", SecretStr("secret"))

    def rechazar(*_args):
        raise InvalidWebhookSignatureError(SignatureFailureReason.SIGNATURE_MISMATCH)

    monkeypatch.setattr(router_suscripciones.WebhookSignatureValidator, "validate", rechazar)
    respuesta = client.post(
        "/webhooks/mercadopago/suscripciones?data.id=1",
        headers={"x-signature": "incorrecta", "x-request-id": "req"},
        json={"type": "subscription_preapproval", "data": {"id": "1"}},
    )
    assert respuesta.status_code == 401