from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from tests.conftest import SessionTest
from app.models.disponibilidad import Disponibilidad
from app.models.disponibilidad_excepcion import DisponibilidadExcepcion
from app.models.especialidad import Especialidad
from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.profesional_especialidad import ProfesionalEspecialidad
from app.models.turno import Turno
from app.core.datetime_utils import fecha_hora_civil_a_utc, utc_a_zona_negocio

ZONA = ZoneInfo("America/Argentina/Buenos_Aires")

def escenario(db, *, duracion=30):
    especialidad = Especialidad(nombre="F11D Clínica", duracion_turno_minutos=30)
    profesional = Profesional(nombre="Laura", apellido="Gómez", matricula="F11D-A", reserva_online_activa=True, slug_publico="laura-gomez-f11d")
    otro = Profesional(nombre="Mario", apellido="López", matricula="F11D-B", reserva_online_activa=True, slug_publico="mario-lopez-f11d")
    db.add_all([especialidad, profesional, otro]); db.flush()
    db.add_all([ProfesionalEspecialidad(profesional_id=profesional.id, especialidad_id=especialidad.id), ProfesionalEspecialidad(profesional_id=otro.id, especialidad_id=especialidad.id)])
    propia = Prestacion(nombre="Consulta", duracion_minutos=duracion, precio=Decimal("100"), modalidad="presencial", profesional_id=profesional.id, especialidad_id=especialidad.id, activa=True, habilitada_online=True)
    ajena = Prestacion(nombre="Ajena", duracion_minutos=30, precio=Decimal("100"), modalidad="presencial", profesional_id=otro.id, especialidad_id=especialidad.id, activa=True, habilitada_online=True)
    db.add_all([propia, ajena]); db.commit(); db.refresh(propia); db.refresh(ajena)
    return profesional, otro, propia, ajena

def consultar(client, profesional, prestacion, desde, hasta=None):
    hasta = hasta or desde
    return client.get(f"/public/profesionales/{profesional.slug_publico}/disponibilidad", params={"prestacion": prestacion.identificador_publico, "fecha_desde": desde.isoformat(), "fecha_hasta": hasta.isoformat()})

def test_consulta_publica_genera_slots_y_timestamps_con_offset(client, monkeypatch):
    db=SessionTest(); profesional, _, prestacion, _=escenario(db)
    ahora=datetime(2026, 9, 10, 8, 0, tzinfo=ZONA); monkeypatch.setattr("app.services.public_booking_service.ahora_negocio", lambda: ahora)
    db.add(Disponibilidad(profesional_id=profesional.id, dia_semana=3, hora_inicio=time(10), hora_fin=time(11))); db.commit()
    respuesta=consultar(client, profesional, prestacion, date(2026,9,10))
    assert respuesta.status_code == 200
    horarios=respuesta.json()["dias"][0]["horarios"]; assert len(horarios)==2
    assert all("-03:00" in item for item in horarios)

def test_excepciones_y_turnos_aplican_a_la_disponibilidad(client, monkeypatch):
    db=SessionTest(); profesional, otro, prestacion, _=escenario(db); fecha=date(2026,9,10)
    monkeypatch.setattr("app.services.public_booking_service.ahora_negocio", lambda: datetime(2026,9,10,8,tzinfo=ZONA))
    db.add_all([Disponibilidad(profesional_id=profesional.id,dia_semana=3,hora_inicio=time(10),hora_fin=time(12)), Disponibilidad(profesional_id=otro.id,dia_semana=3,hora_inicio=time(10),hora_fin=time(12))]); db.commit()
    paciente=Paciente(nombre="Paciente",apellido="Prueba",activo=True); db.add(paciente); db.flush()
    inicio = fecha_hora_civil_a_utc(fecha, time(10))
    fin = fecha_hora_civil_a_utc(fecha, time(10, 30))
    db.add(Turno(paciente_id=paciente.id,prestacion_id=prestacion.id,profesional_id=profesional.id,fecha_hora=inicio,fecha_fin=fin,estado="reservado")); db.commit()
    horarios=consultar(client,profesional,prestacion,fecha).json()["dias"][0]["horarios"]
    assert horarios == [
        utc_a_zona_negocio(fecha_hora_civil_a_utc(fecha, time(10, 30))).isoformat(),
        utc_a_zona_negocio(fecha_hora_civil_a_utc(fecha, time(11))).isoformat(),
        utc_a_zona_negocio(fecha_hora_civil_a_utc(fecha, time(11, 30))).isoformat(),
    ]
    db.query(Turno).delete(); db.add(DisponibilidadExcepcion(profesional_id=profesional.id,fecha=fecha,tipo="cierre_dia",origen="manual",activa=True)); db.commit()
    assert consultar(client,profesional,prestacion,fecha).json()["dias"][0]["horarios"] == []

def test_franja_extraordinaria_y_dia_sin_horarios(client, monkeypatch):
    db=SessionTest(); profesional, _, prestacion, _=escenario(db); fecha=date(2026,9,11)
    monkeypatch.setattr("app.services.public_booking_service.ahora_negocio", lambda: datetime(2026,9,10,8,tzinfo=ZONA))
    db.add(DisponibilidadExcepcion(profesional_id=profesional.id,fecha=fecha,tipo="franja_extraordinaria",origen="manual",hora_inicio=time(10),hora_fin=time(11),activa=True)); db.commit()
    respuesta=consultar(client,profesional,prestacion,fecha); assert len(respuesta.json()["dias"][0]["horarios"])==2
    sin=consultar(client,profesional,prestacion,date(2026,9,12)); assert sin.json()["dias"][0]["horarios"] == []

def test_politica_temporal_y_ventana_inclusiva(client, monkeypatch):
    db=SessionTest(); profesional, _, prestacion, _=escenario(db); ahora=datetime(2026,9,10,23,0,tzinfo=ZONA)
    monkeypatch.setattr("app.services.public_booking_service.ahora_negocio", lambda: ahora)
    assert consultar(client,profesional,prestacion,date(2026,9,9)).status_code == 400
    assert consultar(client,profesional,prestacion,date(2026,9,10),date(2026,11,8)).status_code == 200
    assert consultar(client,profesional,prestacion,date(2026,9,10),date(2026,11,9)).status_code == 400
    assert consultar(client,profesional,prestacion,date(2026,9,11),date(2026,9,10)).status_code == 400

@pytest.mark.parametrize("campo", ["profesional_id", "prestacion_id", "cuenta_id", "paciente", "turnos", "estado"])
def test_respuesta_no_expone_datos_internos(client, monkeypatch, campo):
    db=SessionTest(); profesional, _, prestacion, _=escenario(db); monkeypatch.setattr("app.services.public_booking_service.ahora_negocio", lambda: datetime(2026,9,10,8,tzinfo=ZONA))
    db.add(Disponibilidad(profesional_id=profesional.id,dia_semana=3,hora_inicio=time(10),hora_fin=time(11))); db.commit()
    assert campo not in consultar(client,profesional,prestacion,date(2026,9,10)).text
