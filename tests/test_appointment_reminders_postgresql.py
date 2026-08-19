import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from threading import Barrier

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.models.appointment_reminder import AppointmentReminder
from app.models.cuenta import Cuenta
from app.models.especialidad import Especialidad
from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.turno import Turno
from app.repositories.appointment_reminder_repository import reclamar_vencidos

POSTGRES_URL = os.getenv("TEST_POSTGRES_REMINDERS_URL")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason="Requiere TEST_POSTGRES_REMINDERS_URL con PostgreSQL real.",
)

engine_postgresql = create_engine(POSTGRES_URL, pool_size=8) if POSTGRES_URL else None
SessionPostgresql = sessionmaker(bind=engine_postgresql, expire_on_commit=False) if engine_postgresql else None


@pytest.fixture
def turno_postgresql():
    sufijo = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
    with SessionPostgresql() as db:
        cuenta = Cuenta(nombre=f"Cuenta reminders {sufijo}", tipo="individual")
        paciente = Paciente(nombre="Test", apellido=f"Paciente {sufijo}", dni=None, telefono="3515551234")
        profesional = Profesional(nombre="Test", apellido=f"Profesional {sufijo}", matricula=f"MP-REM-{sufijo}", cuenta=cuenta)
        especialidad = Especialidad(nombre=f"Especialidad {sufijo}", duracion_turno_minutos=30)
        db.add_all([cuenta, paciente, profesional, especialidad])
        db.flush()
        prestacion = Prestacion(
            nombre=f"Consulta {sufijo}", duracion_minutos=30, precio=Decimal("1.00"),
            modalidad="presencial", profesional_id=profesional.id, especialidad_id=especialidad.id,
        )
        db.add(prestacion)
        db.flush()
        turno = Turno(
            paciente_id=paciente.id, prestacion_id=prestacion.id, profesional_id=profesional.id,
            fecha_hora=datetime.now(UTC) + timedelta(days=2),
            fecha_fin=datetime.now(UTC) + timedelta(days=2, minutes=30),
        )
        db.add(turno)
        db.commit()
        turno_id = turno.id
    yield turno_id
    with SessionPostgresql() as db:
        db.execute(text("DELETE FROM appointment_reminders WHERE turno_id = :id"), {"id": turno_id})
        db.execute(text("DELETE FROM turnos WHERE id = :id"), {"id": turno_id})
        db.commit()


def crear_reminder(db, turno_id, sufijo, status="pending"):
    ahora = datetime.now(UTC)
    item = AppointmentReminder(
        turno_id=turno_id, channel="email", reminder_type="24h", status=status,
        appointment_datetime_snapshot=ahora + timedelta(days=2),
        recipient_email_snapshot=f"test-{sufijo}@example.com",
        patient_name_snapshot="Test Paciente", professional_name_snapshot="Test Profesional",
        specialty_name_snapshot="Test Especialidad", service_name_snapshot="Test Servicio",
        scheduled_for=ahora - timedelta(minutes=1),
    )
    db.add(item)
    db.flush()
    return item


def test_unique_real_postgresql(turno_postgresql):
    with SessionPostgresql() as db:
        primero = crear_reminder(db, turno_postgresql, "unique")
        db.commit()
        segundo = AppointmentReminder(
            turno_id=turno_postgresql, channel="email", reminder_type="24h",
            status="pending", appointment_datetime_snapshot=primero.appointment_datetime_snapshot,
            recipient_email_snapshot="otro@example.com", patient_name_snapshot="Test Paciente",
            professional_name_snapshot="Test Profesional", specialty_name_snapshot="Test Especialidad",
            service_name_snapshot="Test Servicio", scheduled_for=primero.scheduled_for,
        )
        db.add(segundo)
        with pytest.raises(IntegrityError) as error:
            db.commit()
        assert "uq_appointment_reminders_occurrence" in str(error.value)
        db.rollback()
        assert db.query(AppointmentReminder).filter(AppointmentReminder.turno_id == turno_postgresql).count() == 1


def ejecutar_claim(reminder_id, barrera):
    ahora = datetime.now(UTC)
    with SessionPostgresql() as db:
        barrera.wait()
        items = reclamar_vencidos(db, ahora, limite=1, confirmar=False)
        ids = [item.id for item in items]
        db.commit()
        return ids


def test_skip_locked_mismo_reminder(turno_postgresql):
    with SessionPostgresql() as db:
        crear_reminder(db, turno_postgresql, "same")
        db.commit()
    barrera = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = list(pool.map(lambda _: ejecutar_claim(1, barrera), (0, 1)))
    obtenidos = [item for resultado in resultados for item in resultado]
    assert len(obtenidos) == 1
    with SessionPostgresql() as db:
        item = db.get(AppointmentReminder, obtenidos[0])
        assert item.status == "processing"
        assert item.processing_started_at is not None


def test_skip_locked_dos_reminders(turno_postgresql):
    with SessionPostgresql() as db:
        crear_reminder(db, turno_postgresql, "one")
        crear_reminder(db, turno_postgresql, "two")
        db.commit()
    barrera = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = list(pool.map(lambda _: ejecutar_claim(1, barrera), (0, 1)))
    obtenidos = [item for resultado in resultados for item in resultado]
    assert len(obtenidos) == 2
    assert len(set(obtenidos)) == 2
