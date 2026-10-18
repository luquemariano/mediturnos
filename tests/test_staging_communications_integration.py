from datetime import UTC, datetime, timedelta
from decimal import Decimal

from pydantic import SecretStr

from app.core.config import settings
from app.integrations.messaging import FakeMessagingProvider
from app.models.cuenta import Cuenta
from app.models.especialidad import Especialidad
from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.turno import Turno
from app.services.whatsapp_appointment_reminder_service import send_whatsapp_appointment_reminder
from tests.conftest import SessionTest


def test_fake_whatsapp_reminder_links_confirm_and_cancel_through_http(client, monkeypatch):
    secret = "synthetic-staging-action-secret-000000000000"
    monkeypatch.setattr(settings, "appointment_action_secret", SecretStr(secret))
    now = datetime.now(UTC)
    with SessionTest() as db:
        cuenta = Cuenta(nombre="Fixture sintético comunicaciones", tipo="individual")
        profesional = Profesional(nombre="Profesional QA", apellido="Sintético", matricula="QA-COMMS-01", cuenta=cuenta)
        paciente = Paciente(
            nombre="Paciente", apellido="Sintético", telefono="3515550101",
            whatsapp_opt_in=True, email="qa-patient@example.test", activo=True,
        )
        especialidad = Especialidad(nombre="Especialidad QA comunicaciones", duracion_turno_minutos=30)
        db.add_all([cuenta, profesional, paciente, especialidad])
        db.flush()
        prestacion = Prestacion(
            nombre="Prestación QA comunicaciones", duracion_minutos=30,
            precio=Decimal("1.00"), modalidad="presencial",
            profesional_id=profesional.id, especialidad_id=especialidad.id,
        )
        db.add(prestacion)
        db.flush()
        turns = [
            Turno(paciente_id=paciente.id, prestacion_id=prestacion.id, profesional_id=profesional.id,
                  fecha_hora=now + timedelta(days=2, hours=index),
                  fecha_fin=now + timedelta(days=2, hours=index, minutes=30), estado="reservado")
            for index in (1, 2)
        ]
        db.add_all(turns)
        db.commit()
        turn_ids = [turn.id for turn in turns]

        provider = FakeMessagingProvider()
        config = type("FakeStagingConfig", (), {
            "app_env": "staging", "whatsapp_enabled": True, "whatsapp_provider": "fake",
            "appointment_action_secret": SecretStr(secret),
        })()
        sent = [send_whatsapp_appointment_reminder(db, turn_id, provider=provider, config=config) for turn_id in turn_ids]
        assert [item.status for item in sent] == ["sent", "sent"]
        assert len(provider.sent_messages) == 2
        confirm_token = provider.sent_messages[0].payload["confirm_token"]
        cancel_token = provider.sent_messages[1].payload["cancel_token"]

    assert client.get("/turnos/public/confirmar", params={"token": confirm_token}).status_code == 200
    confirmed = client.post("/turnos/public/confirmar", params={"token": confirm_token})
    confirmed_again = client.post("/turnos/public/confirmar", params={"token": confirm_token})
    cancelled = client.post("/turnos/public/cancelar", params={"token": cancel_token})
    cancelled_again = client.post("/turnos/public/cancelar", params={"token": cancel_token})
    assert "confirmado correctamente" in confirmed.text
    assert "ya estaba confirmado" in confirmed_again.text
    assert "cancelado correctamente" in cancelled.text
    assert "ya estaba cancelado" in cancelled_again.text
    with SessionTest() as db:
        assert db.get(Turno, turn_ids[0]).estado == "confirmado"
        assert db.get(Turno, turn_ids[1]).estado == "cancelado"
