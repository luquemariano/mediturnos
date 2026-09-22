from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from pydantic import SecretStr

from app.integrations.messaging import FakeMessagingProvider
from app.integrations.messaging import DEFAULT_TEMPLATE_MAPPING
from app.models.message_delivery import MessageDelivery
from app.models.turno import Turno
from app.services.appointment_action_token_service import verify_appointment_action_token
from app.services import whatsapp_appointment_reminder_service as reminder_service
from app.services.whatsapp_appointment_reminder_service import send_whatsapp_appointment_reminder
from tests.conftest import SessionTest


SECRET = "wa7-test-secret"


def config(enabled=True):
    return SimpleNamespace(
        whatsapp_enabled=enabled,
        whatsapp_provider="fake",
        public_api_url="https://api.example.test",
        appointment_action_secret=SecretStr(SECRET),
    )


def turno(**changes):
    fecha = datetime.now(UTC) + timedelta(days=1)
    value = dict(
        id=77,
        estado="reservado",
        fecha_hora=fecha,
        paciente=SimpleNamespace(whatsapp_opt_in=True, whatsapp_opt_out_at=None, telefono="0351 15 1234567"),
        profesional=SimpleNamespace(nombre="Profesional", apellido="Prueba"),
    )
    value.update(changes)
    return SimpleNamespace(**value)


def execute(turn, provider=None, enabled=True):
    db = SessionTest()
    real_get = db.get
    db.get = lambda model, item_id: turn if model is Turno else real_get(model, item_id)
    result = send_whatsapp_appointment_reminder(db, turn.id, provider=provider or FakeMessagingProvider(), config=config(enabled))
    return db, result


def test_disabled_and_ineligible_do_not_create_delivery():
    db, result = execute(turno(), enabled=False); assert result.status == "feature_disabled"; db.close()
    for patient in (SimpleNamespace(whatsapp_opt_in=False, whatsapp_opt_out_at=None, telefono="0351 15 1234567"), SimpleNamespace(whatsapp_opt_in=True, whatsapp_opt_out_at=datetime.now(UTC), telefono="0351 15 1234567"), SimpleNamespace(whatsapp_opt_in=True, whatsapp_opt_out_at=None, telefono="123")):
        db, result = execute(turno(paciente=patient)); assert result.status == "not_eligible"; assert db.query(MessageDelivery).count() == 0; db.close()


def test_cancelled_and_finished_do_not_send():
    for status in ("cancelado", "finalizado", "ausente"):
        db, result = execute(turno(estado=status)); assert result.status == "not_eligible"; db.close()


def test_eligible_turno_sends_once_and_persists_minimal_payload():
    provider = FakeMessagingProvider(); turn = turno()
    db, result = execute(turn, provider); assert result.status == "sent"; assert len(provider.sent_messages) == 1
    item = db.get(MessageDelivery, result.delivery_id)
    message = provider.sent_messages[0]
    assert item.status == "sent" and item.provider == "fake" and item.provider_message_id
    assert item.recipient_snapshot == "5493511234567" and "payload" not in item.__dict__
    assert set(message.payload) == {"appointment_datetime", "professional_name", "confirm_token", "cancel_token"}
    assert "diagnostico" not in str(message.payload).lower() and "observaciones" not in str(message.payload).lower()
    confirm = message.payload["confirm_token"]
    cancel = message.payload["cancel_token"]
    assert verify_appointment_action_token(token=confirm, secret=SECRET, expected_scope="confirm")["turno_id"] == turn.id
    assert verify_appointment_action_token(token=cancel, secret=SECRET, expected_scope="cancel")["turno_id"] == turn.id
    assert confirm not in repr(item) and cancel not in repr(item)
    assert item.recipient_snapshot not in (confirm, cancel)
    db.close()


def test_second_attempt_after_sent_is_idempotent_and_date_change_gets_new_key():
    provider = FakeMessagingProvider(); turn = turno(); db, first = execute(turn, provider)
    second = send_whatsapp_appointment_reminder(db, turn.id, provider=provider, config=config())
    assert first.delivery_id == second.delivery_id and second.status == "already_sent" and len(provider.sent_messages) == 1
    turn.fecha_hora += timedelta(days=1)
    third = send_whatsapp_appointment_reminder(db, turn.id, provider=provider, config=config())
    assert third.status == "sent" and third.delivery_id != first.delivery_id and len(provider.sent_messages) == 2
    db.close()


def test_provider_failure_marks_failed_and_not_processing():
    provider = FakeMessagingProvider(fail_next=True); db, result = execute(turno(), provider)
    item = db.get(MessageDelivery, result.delivery_id)
    assert result.status == "failed" and item.status == "failed" and item.processing_started_at is None
    assert item.last_error and "secret" not in item.last_error.lower()
    db.close()


def test_meta_config_se_pasa_al_factory_con_mapping(monkeypatch):
    turn = turno()
    meta_config = config()
    meta_config.whatsapp_provider = "meta"
    meta_config.whatsapp_api_version = "v99.0"
    meta_config.whatsapp_phone_number_id = "test-phone-id"
    meta_config.whatsapp_access_token = SecretStr("test-access-token")
    captured = {}
    provider = FakeMessagingProvider()

    def factory(provider_name, **values):
        captured["provider_name"] = provider_name
        captured.update(values)
        return provider

    monkeypatch.setattr(reminder_service, "get_messaging_provider", factory)
    db = SessionTest()
    real_get = db.get
    db.get = lambda model, item_id: turn if model is Turno else real_get(model, item_id)

    result = send_whatsapp_appointment_reminder(db, turn.id, config=meta_config)

    assert result.status == "sent"
    assert captured["provider_name"] == "meta"
    assert captured["api_version"] == "v99.0"
    assert captured["phone_number_id"] == "test-phone-id"
    assert captured["access_token"] == meta_config.whatsapp_access_token
    assert captured["template_mapping"] is DEFAULT_TEMPLATE_MAPPING
    assert len(provider.sent_messages) == 1
    db.close()
