from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.datetime_utils import desde_base_utc
from app.main import app
from app.models.especialidad import Especialidad
from app.models.paciente import Paciente
from app.models.pago import Pago
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.turno import Turno
from app.models.usuario import Usuario
from app.services import pago_service
from tests.conftest import SessionTest


class RecursoPago:
    def __init__(self, respuesta):
        self.respuesta = respuesta

    def get(self, _payment_id):
        return {"status": 200, "response": self.respuesta}


class RecursoOrden:
    def __init__(self, preference_id):
        self.preference_id = preference_id

    def get(self, _order_id):
        return {
            "status": 200,
            "response": {"preference_id": self.preference_id},
        }


class SDKPago:
    def __init__(self, respuesta, preference_id):
        self._pago = RecursoPago(respuesta)
        self._orden = RecursoOrden(preference_id)

    def payment(self):
        return self._pago

    def merchant_order(self):
        return self._orden


@pytest.fixture
def escenario_webhook(monkeypatch):
    db = SessionTest()
    usuario = Usuario(
        nombre="Administrador",
        email="admin-pagos@example.com",
        password_hash="hash",
        rol="administrador",
    )
    paciente = Paciente(
        nombre="Paciente",
        apellido="Pagos",
        dni="30999111",
        telefono="3515550000",
    )
    profesional = Profesional(
        nombre="Profesional",
        apellido="Pagos",
        matricula="MP-WEBHOOK-001",
    )
    especialidad = Especialidad(
        nombre="Especialidad pagos",
        duracion_turno_minutos=30,
    )
    db.add_all([
        usuario,
        paciente,
        profesional,
        especialidad,
    ])
    db.flush()
    prestacion = Prestacion(
        nombre="Consulta de pagos",
        duracion_minutos=30,
        precio=Decimal("15000.00"),
        modalidad="presencial",
        profesional_id=profesional.id,
        especialidad_id=especialidad.id,
    )
    db.add(prestacion)
    db.flush()
    inicio = datetime.now(UTC) + timedelta(days=5)
    turno = Turno(
        paciente_id=paciente.id,
        prestacion_id=prestacion.id,
        profesional_id=profesional.id,
        fecha_hora=inicio,
        fecha_fin=inicio + timedelta(minutes=30),
    )
    db.add(turno)
    db.flush()
    pago = Pago(
        turno_id=turno.id,
        preference_id="pref-webhook-001",
        estado="pendiente",
        monto=Decimal("15000.00"),
        init_point="https://example.com/pagar",
    )
    db.add(pago)
    db.commit()
    monkeypatch.setattr(
        settings,
        "mercado_pago_access_token",
        "token-test",
    )

    yield {
        "db": db,
        "pago": pago,
        "turno": turno,
        "usuario": usuario,
    }

    db.close()


def datos_pago(
    escenario,
    estado="approved",
    actualizado=None,
    payment_id="payment-001",
):
    pago = escenario["pago"]
    turno = escenario["turno"]

    return {
        "id": payment_id,
        "status": estado,
        "external_reference": str(turno.id),
        "transaction_amount": "15000.00",
        "currency_id": "ARS",
        "date_last_updated": (
            actualizado or datetime(2026, 8, 12, tzinfo=UTC)
        ).isoformat(),
        "metadata": {
            "pago_id": pago.id,
            "turno_id": turno.id,
        },
        "order": {"id": "merchant-order-001"},
    }


def configurar_sdk(monkeypatch, escenario, datos):
    sdk = SDKPago(datos, escenario["pago"].preference_id)
    monkeypatch.setattr(
        pago_service.mercadopago,
        "SDK",
        lambda _token: sdk,
    )


def test_webhook_aprobado_confirma_turno(
    escenario_webhook,
    monkeypatch,
):
    datos = datos_pago(escenario_webhook)
    configurar_sdk(monkeypatch, escenario_webhook, datos)

    pago = pago_service.procesar_notificacion_pago(
        escenario_webhook["db"],
        "payment-001",
    )

    assert pago.estado == "approved"
    assert pago.requiere_revision is False
    assert pago.motivo_revision is None
    assert pago.turno.estado == "confirmado"


def test_webhook_repetido_es_idempotente(
    escenario_webhook,
    monkeypatch,
):
    datos = datos_pago(escenario_webhook)
    configurar_sdk(monkeypatch, escenario_webhook, datos)
    db = escenario_webhook["db"]

    primero = pago_service.procesar_notificacion_pago(
        db,
        "payment-001",
    )
    actualizado_en = primero.actualizado_en
    segundo = pago_service.procesar_notificacion_pago(
        db,
        "payment-001",
    )

    assert segundo.id == primero.id
    assert segundo.estado == "approved"
    assert segundo.turno.estado == "confirmado"
    assert segundo.actualizado_en == actualizado_en


def test_webhook_legacy_se_asocia_por_turno_y_preferencia(
    escenario_webhook,
    monkeypatch,
):
    datos = datos_pago(escenario_webhook)
    datos["metadata"] = {}
    configurar_sdk(monkeypatch, escenario_webhook, datos)

    pago = pago_service.procesar_notificacion_pago(
        escenario_webhook["db"],
        "payment-001",
    )

    assert pago.id == escenario_webhook["pago"].id
    assert pago.estado == "approved"


@pytest.mark.parametrize(
    "estado_turno",
    ["confirmado", "cancelado"],
)
def test_webhook_aprobado_confirma_estado_no_terminal(
    escenario_webhook,
    monkeypatch,
    estado_turno,
):
    db = escenario_webhook["db"]
    escenario_webhook["turno"].estado = estado_turno
    db.commit()
    datos = datos_pago(escenario_webhook)
    configurar_sdk(monkeypatch, escenario_webhook, datos)

    pago = pago_service.procesar_notificacion_pago(
        db,
        "payment-001",
    )

    assert pago.turno.estado == "confirmado"


@pytest.mark.parametrize("estado_turno", ["finalizado", "ausente"])
@pytest.mark.parametrize("estado_pago", ["approved", "refunded"])
def test_webhook_no_degrada_estados_terminales(
    escenario_webhook,
    monkeypatch,
    estado_turno,
    estado_pago,
):
    db = escenario_webhook["db"]
    escenario_webhook["turno"].estado = estado_turno
    db.commit()
    datos = datos_pago(
        escenario_webhook,
        estado=estado_pago,
    )
    configurar_sdk(monkeypatch, escenario_webhook, datos)

    pago = pago_service.procesar_notificacion_pago(
        db,
        "payment-001",
    )

    assert pago.estado == estado_pago
    assert pago.turno.estado == estado_turno


def test_evento_antiguo_no_retrocede_estado(
    escenario_webhook,
    monkeypatch,
):
    db = escenario_webhook["db"]
    fecha_nueva = datetime(2026, 8, 12, 12, tzinfo=UTC)
    datos_nuevos = datos_pago(
        escenario_webhook,
        actualizado=fecha_nueva,
    )
    configurar_sdk(monkeypatch, escenario_webhook, datos_nuevos)
    pago_service.procesar_notificacion_pago(db, "payment-001")

    datos_viejos = datos_pago(
        escenario_webhook,
        estado="refunded",
        actualizado=fecha_nueva - timedelta(hours=1),
    )
    configurar_sdk(monkeypatch, escenario_webhook, datos_viejos)
    pago = pago_service.procesar_notificacion_pago(
        db,
        "payment-001",
    )

    assert pago.estado == "approved"
    assert pago.turno.estado == "confirmado"


@pytest.mark.parametrize(
    "estado_nuevo",
    ["rejected", "approved"],
)
def test_pago_aprobado_ignora_otro_payment_id(
    escenario_webhook,
    monkeypatch,
    estado_nuevo,
):
    db = escenario_webhook["db"]
    pago = escenario_webhook["pago"]
    turno = escenario_webhook["turno"]
    fecha_consolidada = datetime(2026, 8, 12, 12, tzinfo=UTC)
    pago.payment_id = "payment-consolidado"
    pago.estado = "approved"
    pago.mp_actualizado_en = fecha_consolidada
    turno.estado = "confirmado"
    db.commit()
    actualizado_en = pago.actualizado_en
    datos = datos_pago(
        escenario_webhook,
        estado=estado_nuevo,
        actualizado=fecha_consolidada + timedelta(hours=1),
        payment_id="payment-otro",
    )
    configurar_sdk(monkeypatch, escenario_webhook, datos)

    resultado = pago_service.procesar_notificacion_pago(
        db,
        "payment-otro",
    )

    assert resultado.payment_id == "payment-consolidado"
    assert resultado.estado == "approved"
    assert desde_base_utc(
        resultado.mp_actualizado_en
    ) == fecha_consolidada
    assert resultado.turno.estado == "confirmado"
    assert resultado.actualizado_en == actualizado_en


def test_nuevo_payment_id_aprobado_reemplaza_intento_no_aprobado(
    escenario_webhook,
    monkeypatch,
):
    db = escenario_webhook["db"]
    pago = escenario_webhook["pago"]
    pago.payment_id = "payment-rechazado"
    pago.estado = "rejected"
    pago.mp_actualizado_en = datetime(
        2026, 8, 12, 15, tzinfo=UTC
    )
    db.commit()
    datos = datos_pago(
        escenario_webhook,
        estado="approved",
        actualizado=datetime(2026, 8, 12, 14, tzinfo=UTC),
        payment_id="payment-aprobado",
    )
    configurar_sdk(monkeypatch, escenario_webhook, datos)

    resultado = pago_service.procesar_notificacion_pago(
        db,
        "payment-aprobado",
    )

    assert resultado.payment_id == "payment-aprobado"
    assert resultado.estado == "approved"
    assert desde_base_utc(
        resultado.mp_actualizado_en
    ) == datetime(2026, 8, 12, 14, tzinfo=UTC)
    assert resultado.turno.estado == "confirmado"


def test_otro_payment_id_negativo_no_reemplaza_intento_vigente(
    escenario_webhook,
    monkeypatch,
):
    db = escenario_webhook["db"]
    pago = escenario_webhook["pago"]
    pago.payment_id = "payment-pendiente"
    pago.estado = "pending"
    pago.mp_actualizado_en = datetime(
        2026, 8, 12, 12, tzinfo=UTC
    )
    db.commit()
    datos = datos_pago(
        escenario_webhook,
        estado="rejected",
        actualizado=datetime(2026, 8, 12, 13, tzinfo=UTC),
        payment_id="payment-rechazado",
    )
    configurar_sdk(monkeypatch, escenario_webhook, datos)

    resultado = pago_service.procesar_notificacion_pago(
        db,
        "payment-rechazado",
    )

    assert resultado.payment_id == "payment-pendiente"
    assert resultado.estado == "pending"
    assert resultado.turno.estado == "reservado"


def test_fecha_de_otro_intento_no_impide_reemplazo_aprobado(
    escenario_webhook,
    monkeypatch,
):
    db = escenario_webhook["db"]
    pago = escenario_webhook["pago"]
    pago.payment_id = "payment-anterior"
    pago.estado = "rejected"
    pago.mp_actualizado_en = datetime(
        2026, 8, 12, 18, tzinfo=UTC
    )
    db.commit()
    datos = datos_pago(
        escenario_webhook,
        estado="approved",
        actualizado=datetime(2026, 8, 12, 17, tzinfo=UTC),
        payment_id="payment-nuevo",
    )
    configurar_sdk(monkeypatch, escenario_webhook, datos)

    resultado = pago_service.procesar_notificacion_pago(
        db,
        "payment-nuevo",
    )

    assert resultado.payment_id == "payment-nuevo"
    assert resultado.estado == "approved"


def test_webhook_rechaza_preferencia_incorrecta(
    escenario_webhook,
    monkeypatch,
):
    datos = datos_pago(escenario_webhook)
    sdk = SDKPago(datos, "pref-de-otro-intento")
    monkeypatch.setattr(
        pago_service.mercadopago,
        "SDK",
        lambda _token: sdk,
    )

    with pytest.raises(HTTPException) as error:
        pago_service.procesar_notificacion_pago(
            escenario_webhook["db"],
            "payment-001",
        )

    assert error.value.status_code == 409


def test_webhook_rechaza_id_firmado_distinto_del_body(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "mercado_pago_webhook_secret",
        "secret-test",
    )
    monkeypatch.setattr(
        "app.routers.pagos.WebhookSignatureValidator.validate",
        lambda *_args, **_kwargs: None,
    )

    respuesta = client.post(
        "/pagos/webhook?data.id=payment-firmado",
        headers={
            "x-signature": "firma",
            "x-request-id": "request-1",
        },
        json={
            "type": "payment",
            "data": {"id": "payment-distinto"},
        },
    )

    assert respuesta.status_code == 400


def test_error_persistencia_del_webhook_no_responde_200(
    monkeypatch,
):
    monkeypatch.setattr(
        settings,
        "mercado_pago_webhook_secret",
        "secret-test",
    )
    monkeypatch.setattr(
        "app.routers.pagos.WebhookSignatureValidator.validate",
        lambda *_args, **_kwargs: None,
    )

    def persistencia_fallida(*_args, **_kwargs):
        raise RuntimeError("fallo de persistencia")

    monkeypatch.setattr(
        "app.routers.pagos.procesar_notificacion_pago",
        persistencia_fallida,
    )

    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as client:
        respuesta = client.post(
            "/pagos/webhook?data.id=payment-001",
            headers={
                "x-signature": "firma",
                "x-request-id": "request-1",
            },
            json={
                "type": "payment",
                "data": {"id": "payment-001"},
            },
        )

    assert respuesta.status_code == 500
