from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.appointment_reminder import AppointmentReminder
from app.repositories.appointment_reminder_repository import (
    buscar_ocurrencia,
    crear_recordatorio,
    listar_candidatos_programados,
    listar_por_turno,
)
from app.services.appointment_reminder_service import claim_due_reminders
from tests.conftest import SessionTest


def nuevo(**cambios):
    valores = {
        "turno_id": 10,
        "appointment_datetime_snapshot": datetime(2026, 8, 20, 13, tzinfo=UTC),
        "recipient_email_snapshot": "paciente@example.com",
        "patient_name_snapshot": "Ana Pérez",
        "professional_name_snapshot": "Dr. Juan Pérez",
        "specialty_name_snapshot": "Cardiología",
        "service_name_snapshot": "Consulta",
        "scheduled_for": datetime(2026, 8, 19, 13, tzinfo=UTC),
    }
    valores.update(cambios)
    return AppointmentReminder(**valores)


def test_defaults_y_campos_nullable():
    item = nuevo()
    with SessionTest() as db:
        db.add(item)
        db.commit()
        db.refresh(item)
        assert item.channel == "email"
        assert item.reminder_type == "24h"
        assert item.status == "pending"
        assert item.attempt_count == 0
    assert item.sent_at is None
    assert item.provider_message_id is None


def test_unique_impide_repetir_misma_ocurrencia():
    with SessionTest() as db:
        db.add_all([nuevo(), nuevo()])
        with pytest.raises(IntegrityError):
            db.commit()


def test_unique_permite_nueva_fecha_y_otro_canal():
    with SessionTest() as db:
        db.add_all([
            nuevo(),
            nuevo(appointment_datetime_snapshot=datetime(2026, 8, 22, 18, tzinfo=UTC)),
            nuevo(channel="whatsapp"),
        ])
        db.commit()
        assert len(listar_por_turno(db, 10)) == 3


def test_repository_busca_ocurrencia_y_candidatos():
    ahora = datetime.now(UTC)
    with SessionTest() as db:
        item = nuevo(scheduled_for=ahora - timedelta(minutes=1))
        crear_recordatorio(db, item)
        db.commit()
        assert buscar_ocurrencia(
            db, 10, "email", "24h", item.appointment_datetime_snapshot
        ).id == item.id
        assert [c.id for c in listar_candidatos_programados(db, ahora)] == [item.id]


def test_claim_filtra_estado_fecha_y_reintento():
    ahora = datetime.now(UTC)
    with SessionTest() as db:
        vencido = nuevo(turno_id=20, scheduled_for=ahora - timedelta(minutes=1))
        futuro = nuevo(turno_id=21, scheduled_for=ahora + timedelta(minutes=1))
        retry_futuro = nuevo(
            turno_id=22,
            scheduled_for=ahora - timedelta(minutes=1),
            next_attempt_at=ahora + timedelta(minutes=5),
        )
        sent = nuevo(turno_id=23, scheduled_for=ahora - timedelta(minutes=1), status="sent")
        skipped = nuevo(turno_id=24, scheduled_for=ahora - timedelta(minutes=1), status="skipped")
        failed = nuevo(turno_id=25, scheduled_for=ahora - timedelta(minutes=1), status="failed")
        processing = nuevo(turno_id=26, scheduled_for=ahora - timedelta(minutes=1), status="processing")
        db.add_all([vencido, futuro, retry_futuro, sent, skipped, failed, processing])
        db.commit()
        claimed = claim_due_reminders(db, ahora)
        assert [item.turno_id for item in claimed] == [20]
        assert claimed[0].status == "processing"
        assert claimed[0].processing_started_at is not None
