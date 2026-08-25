from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.models.appointment_reminder import AppointmentReminder
from app.services.appointment_reminder_service import (
    _email_normalizado,
    recover_stale_processing,
    schedule_retry,
)
from app.services import appointment_reminder_service as service
from app.services import email_service
from tests.conftest import SessionTest


def reminder(**changes):
    values = {
        "turno_id": 99,
        "appointment_datetime_snapshot": datetime(2026, 8, 20, 13, tzinfo=UTC),
        "recipient_email_snapshot": "p@example.com",
        "patient_name_snapshot": "Paciente",
        "professional_name_snapshot": "Profesional",
        "specialty_name_snapshot": "Especialidad",
        "service_name_snapshot": "Servicio",
        "scheduled_for": datetime(2026, 8, 19, 13, tzinfo=UTC),
        "status": "processing",
        "processing_started_at": datetime.now(UTC) - timedelta(minutes=30),
    }
    values.update(changes)
    return AppointmentReminder(**values)


def test_email_normalizado_distingue_faltante_invalido_y_valido():
    assert _email_normalizado(None) == (None, "missing_email")
    assert _email_normalizado("   ") == (None, "missing_email")
    assert _email_normalizado("no-es-email") == (None, "invalid_email")
    assert _email_normalizado("  Persona@Example.COM ") == ("persona@example.com", None)


def test_retry_usa_backoff_y_falla_al_tercer_intento():
    ahora = datetime.now(UTC)
    with SessionTest() as db:
        item = reminder(status="processing", processing_started_at=ahora)
        db.add(item)
        db.commit()
        assert schedule_retry(db, item, "timeout", ahora) == "pending"
        assert item.attempt_count == 1
        assert item.next_attempt_at.replace(tzinfo=UTC) == ahora + timedelta(minutes=5)
        assert schedule_retry(db, item, "timeout", ahora) == "pending"
        assert item.next_attempt_at.replace(tzinfo=UTC) == ahora + timedelta(minutes=30)
        assert schedule_retry(db, item, "timeout", ahora) == "failed"
        assert item.attempt_count == 3


def test_recupera_processing_huerfano_y_no_el_reciente():
    ahora = datetime.now(UTC)
    with SessionTest() as db:
        viejo = reminder(turno_id=100, processing_started_at=ahora - timedelta(minutes=30))
        reciente = reminder(turno_id=101, processing_started_at=ahora - timedelta(minutes=1))
        db.add_all([viejo, reciente])
        db.commit()
        assert recover_stale_processing(db, ahora) == 1
        db.refresh(viejo)
        db.refresh(reciente)
        assert viejo.status == "pending"
        assert reciente.status == "processing"


def turno_para_generacion(fecha, estado="reservado", email="Paciente@Example.com"):
    return SimpleNamespace(
        id=500,
        estado=estado,
        fecha_hora=fecha,
        paciente=SimpleNamespace(nombre="Ana", apellido="Pérez", email=email),
        profesional=SimpleNamespace(nombre="Juan", apellido="Médico"),
        prestacion=SimpleNamespace(
            nombre="Consulta",
            especialidad=SimpleNamespace(nombre="Cardiología"),
        ),
    )


def test_generacion_crea_snapshots_y_es_idempotente(monkeypatch):
    ahora = datetime(2026, 8, 19, 12, tzinfo=UTC)
    turno = turno_para_generacion(ahora + timedelta(hours=20), estado="confirmado")
    monkeypatch.setattr(service, "_turnos_candidatos", lambda *args: [turno])
    with SessionTest() as db:
        primera = service.generate_upcoming_reminders(db, ahora)
        segunda = service.generate_upcoming_reminders(db, ahora)
        assert len(primera) == 1
        assert segunda == []
        item = primera[0]
        assert item.scheduled_for == (turno.fecha_hora - timedelta(hours=24)).replace(tzinfo=None)
        assert item.patient_name_snapshot == "Ana Pérez"
        assert item.professional_name_snapshot == "Juan Médico"
        assert item.specialty_name_snapshot == "Cardiología"
        assert item.service_name_snapshot == "Consulta"
        assert item.recipient_email_snapshot == "paciente@example.com"


def test_generacion_email_invalido_queda_skipped_sin_modificar_paciente(monkeypatch):
    ahora = datetime(2026, 8, 19, 12, tzinfo=UTC)
    turno = turno_para_generacion(ahora + timedelta(hours=20), email="  ")
    email_original = turno.paciente.email
    monkeypatch.setattr(service, "_turnos_candidatos", lambda *args: [turno])
    with SessionTest() as db:
        item = service.generate_upcoming_reminders(db, ahora)[0]
        assert item.status == "skipped"
        assert item.skip_reason == "missing_email"
        assert item.last_error is None
        assert turno.paciente.email == email_original


def test_generacion_email_invalido_y_ausente_separados(monkeypatch):
    ahora = datetime(2026, 8, 19, 12, tzinfo=UTC)
    faltante = turno_para_generacion(ahora + timedelta(hours=20), email=None)
    invalido = turno_para_generacion(ahora + timedelta(hours=21), email="no")
    invalido.id = 501
    monkeypatch.setattr(service, "_turnos_candidatos", lambda *args: [faltante, invalido])
    with SessionTest() as db:
        items = service.generate_upcoming_reminders(db, ahora)
        assert {item.skip_reason for item in items} == {"missing_email", "invalid_email"}


def test_reprogramaciones_consecutivas_crean_una_ocurrencia_por_snapshot(monkeypatch):
    ahora = datetime(2026, 8, 19, 12, tzinfo=UTC)
    turno = turno_para_generacion(ahora + timedelta(hours=20))
    turno.id = 600
    monkeypatch.setattr(service, "_turnos_candidatos", lambda *args: [turno])
    with SessionTest() as db:
        assert len(service.generate_upcoming_reminders(db, ahora)) == 1
        turno.fecha_hora = ahora + timedelta(hours=21)
        assert len(service.generate_upcoming_reminders(db, ahora)) == 1
        assert len(service.generate_upcoming_reminders(db, ahora)) == 0


def test_validacion_cancelacion_reprogramacion_y_pasado():
    ahora = datetime(2026, 8, 19, 12, tzinfo=UTC)
    class Db:
        def __init__(self, turno): self.turno = turno
        def get(self, modelo, _id): return self.turno
        def commit(self): pass

    turno = turno_para_generacion(ahora + timedelta(hours=2))
    item = reminder(turno_id=turno.id, appointment_datetime_snapshot=turno.fecha_hora)
    db = Db(turno)
    turno.estado = "cancelado"
    assert service.process_claimed_reminder(db, item, ahora) == "skipped"
    assert item.skip_reason == "cancelled"
    turno.estado = "reservado"
    turno.fecha_hora += timedelta(days=1)
    item.status = "processing"
    assert service.process_claimed_reminder(db, item, ahora) == "skipped"
    assert item.skip_reason == "rescheduled"
    turno.fecha_hora = ahora - timedelta(minutes=1)
    item.appointment_datetime_snapshot = turno.fecha_hora
    item.status = "processing"
    assert service.process_claimed_reminder(db, item, ahora) == "skipped"
    assert item.skip_reason == "appointment_passed"


def test_send_exitoso_marca_sent_y_usa_snapshot(monkeypatch):
    ahora = datetime(2026, 8, 19, 12, tzinfo=UTC)
    turno = turno_para_generacion(ahora + timedelta(hours=2))
    item = reminder(turno_id=turno.id, appointment_datetime_snapshot=turno.fecha_hora)
    item.status = "processing"

    class Db:
        def get(self, modelo, _id): return turno
        def commit(self): pass

    class Provider:
        def enviar(self, mensaje):
            assert mensaje.destinatario == item.recipient_email_snapshot
            assert item.patient_name_snapshot in mensaje.texto
            return email_service.EmailDeliveryResult("in_memory", "msg-1")

    monkeypatch.setattr(service, "obtener_email_provider", lambda: Provider())
    assert service.send_claimed_reminder(Db(), item, ahora) == "sent"
    assert item.status == "sent"
    assert item.provider == "in_memory"
    assert item.provider_message_id == "msg-1"
    assert item.sent_at == ahora
    assert item.processing_started_at is None
