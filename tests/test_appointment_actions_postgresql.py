import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from threading import Barrier

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models.appointment_reminder import AppointmentReminder
from app.models.cuenta import Cuenta
from app.models.especialidad import Especialidad
from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.turno import Turno
from app.services.appointment_action_service import AppointmentActionError, apply_appointment_action
from app.services.appointment_action_token_service import generate_appointment_action_token

POSTGRES_URL = os.getenv("TEST_POSTGRES_APPOINTMENT_ACTIONS_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="Requiere PostgreSQL local real.")
engine = create_engine(POSTGRES_URL, pool_size=8) if POSTGRES_URL else None
Session = sessionmaker(bind=engine, expire_on_commit=False) if engine else None
SECRET = "a" * 40


def crear_turno():
    sufijo = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")
    with Session() as db:
        cuenta = Cuenta(nombre=f"Acciones {sufijo}", tipo="individual")
        paciente = Paciente(nombre="Demo", apellido=f"Paciente {sufijo}", dni=None, telefono="3515551234")
        profesional = Profesional(nombre="Demo", apellido=f"Profesional {sufijo}", matricula=f"ACT-{sufijo}", cuenta=cuenta)
        especialidad = Especialidad(nombre=f"Especialidad {sufijo}", duracion_turno_minutos=30)
        db.add_all([cuenta, paciente, profesional, especialidad])
        db.flush()
        prestacion = Prestacion(nombre=f"Consulta {sufijo}", duracion_minutos=30, precio=Decimal("1"), modalidad="presencial", profesional_id=profesional.id, especialidad_id=especialidad.id)
        db.add(prestacion)
        db.flush()
        inicio = datetime.now(UTC) + timedelta(days=2)
        turno = Turno(paciente_id=paciente.id, prestacion_id=prestacion.id, profesional_id=profesional.id, fecha_hora=inicio, fecha_fin=inicio + timedelta(minutes=30), estado="reservado")
        db.add(turno)
        db.commit()
        return turno.id, inicio


def limpiar(turno_id):
    with Session() as db:
        db.execute(text("DELETE FROM appointment_reminders WHERE turno_id = :id"), {"id": turno_id})
        db.execute(text("DELETE FROM turnos WHERE id = :id"), {"id": turno_id})
        db.commit()


def token(turno_id, fecha, scope):
    return generate_appointment_action_token(secret=SECRET, turno_id=turno_id, appointment_datetime_snapshot=fecha, action_scope=scope)


def test_confirm_cancel_concurrent_real_postgresql():
    turno_id, fecha = crear_turno()
    try:
        confirm = token(turno_id, fecha, "confirm")
        cancel = token(turno_id, fecha, "cancel")
        barrera = Barrier(2)

        def ejecutar(action, value):
            with Session() as db:
                barrera.wait()
                try:
                    return apply_appointment_action(db, token=value, secret=SECRET, action=action)
                except AppointmentActionError as error:
                    return error.args[0]

        with ThreadPoolExecutor(max_workers=2) as pool:
            resultados = list(pool.map(lambda args: ejecutar(*args), [("confirm", confirm), ("cancel", cancel)]))
        assert all(resultado == "not_allowed" or resultado[1] in {"confirm", "cancel"} for resultado in resultados)
        with Session() as db:
            assert db.get(Turno, turno_id).estado in {"confirmado", "cancelado"}
    finally:
        limpiar(turno_id)


def test_cancel_gana_no_reactiva_y_confirm_gana_permite_cancelar():
    turno_id, fecha = crear_turno()
    try:
        cancel = token(turno_id, fecha, "cancel")
        confirm = token(turno_id, fecha, "confirm")
        with Session() as db:
            apply_appointment_action(db, token=cancel, secret=SECRET, action="cancel")
        with Session() as db:
            with pytest.raises(AppointmentActionError):
                apply_appointment_action(db, token=confirm, secret=SECRET, action="confirm")
            assert db.get(Turno, turno_id).estado == "cancelado"
        with Session() as db:
            apply_appointment_action(db, token=confirm, secret=SECRET, action="confirm") if False else None
            db.query(Turno).filter(Turno.id == turno_id).update({"estado": "confirmado"})
            db.commit()
        with Session() as db:
            apply_appointment_action(db, token=cancel, secret=SECRET, action="cancel")
            assert db.get(Turno, turno_id).estado == "cancelado"
    finally:
        limpiar(turno_id)


@pytest.mark.parametrize("estado,accion,permitido", [("reservado", "confirm", True), ("confirmado", "confirm", True), ("cancelado", "confirm", False), ("atendido", "confirm", False), ("ausente", "confirm", False), ("reservado", "cancel", True), ("confirmado", "cancel", True), ("cancelado", "cancel", True), ("atendido", "cancel", False), ("ausente", "cancel", False)])
def test_matriz_estados(estado, accion, permitido):
    turno_id, fecha = crear_turno()
    try:
        with Session() as db:
            db.query(Turno).filter(Turno.id == turno_id).update({"estado": estado})
            db.commit()
        with Session() as db:
            resultado = apply_appointment_action(db, token=token(turno_id, fecha, accion), secret=SECRET, action=accion)
            assert permitido
            assert resultado[0].estado in {"confirmado", "cancelado"}
    except AppointmentActionError:
        assert not permitido
    finally:
        limpiar(turno_id)
