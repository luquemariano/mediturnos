from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo
from uuid import UUID
import pytest
from tests.conftest import SessionTest
from app.models.disponibilidad import Disponibilidad
from app.models.especialidad import Especialidad
from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.profesional_especialidad import ProfesionalEspecialidad
from app.models.profesional_paciente import ProfesionalPaciente
from app.models.turno import Turno
from app.models.disponibilidad_excepcion import DisponibilidadExcepcion
from app.core.datetime_utils import fecha_hora_civil_a_utc

ZONA=ZoneInfo("America/Argentina/Buenos_Aires")

def escenario(db):
    e=Especialidad(nombre="F11.2 Clínica",duracion_turno_minutos=30); p=Profesional(nombre="Laura",apellido="Gómez",matricula="F112-A",activo=True,reserva_online_activa=True,slug_publico="laura-gomez-f112"); db.add_all([e,p]); db.flush(); db.add(ProfesionalEspecialidad(profesional_id=p.id,especialidad_id=e.id)); s=Prestacion(nombre="Consulta",duracion_minutos=30,precio=Decimal("100"),modalidad="presencial",profesional_id=p.id,especialidad_id=e.id,activa=True,habilitada_online=True); db.add(s); db.commit(); db.refresh(s); return p,s

def payload(s, **paciente): return {"prestacion":s.identificador_publico,"fecha_hora":"2026-09-15T10:30:00-03:00","paciente":{"nombre":"Ana","apellido":"Pérez","email":" ANA@EXAMPLE.COM ",**paciente}}

def test_reserva_publica_crea_turno_paciente_vinculo_y_respuesta_segura(client):
    db=SessionTest(); p,s=escenario(db); db.add(Disponibilidad(profesional_id=p.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(12))); db.commit()
    r=client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=payload(s,telefono=" 123 ")); assert r.status_code==201
    data=r.json(); assert UUID(data["reserva_id"]).version==4 and data["estado"]=="reservado"; assert data["prestacion"]["nombre"]=="Consulta"
    assert data["fecha_hora"].endswith("-03:00") and data["fecha_fin"].endswith("-03:00")
    assert db.query(Paciente).count()==1 and db.query(ProfesionalPaciente).count()==1 and db.query(Turno).count()==1
    for campo in ("id","paciente_id","profesional_id","prestacion_id","cuenta_id","usuario_id","dni","email","telefono","observaciones"): assert campo not in data
    db.close()

def test_rechaza_publicacion_invalida(client):
    db=SessionTest(); p,s=escenario(db); base=payload(s)
    for slug in ("no", p.slug_publico.upper()): assert client.post(f"/public/profesionales/{slug}/reservas",json=base).status_code==404
    db.close()

@pytest.mark.parametrize("campo", ["profesional_id", "prestacion_id", "cuenta_id", "usuario_id", "estado", "fecha_fin", "paciente_id", "identificador_publico"])
def test_payload_extra_rechazado(client, campo):
    db=SessionTest(); p,s=escenario(db); assert client.post(f"/public/profesionales/{p.slug_publico}/reservas",json={**payload(s),campo:1}).status_code==422; db.close()

def test_datetime_naive_rechazado(client):
    db=SessionTest(); p,s=escenario(db); assert client.post(f"/public/profesionales/{p.slug_publico}/reservas",json={**payload(s),"fecha_hora":"2026-09-15T10:30:00"}).status_code==422; db.close()

def test_rate_limit_publico_es_diez_por_ip(client):
    db=SessionTest(); p,s=escenario(db); body=payload(s)
    for _ in range(10): assert client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=body).status_code in (400,409)
    assert client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=body).status_code==429; db.close()

def test_rechaza_slot_fuera_de_disponibilidad_y_menor_a_dos_horas(client,monkeypatch):
    db=SessionTest(); p,s=escenario(db); ahora=datetime(2026,9,15,8,tzinfo=ZONA); monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda:ahora)
    assert client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=payload(s)).status_code in (400,409)
    db.add(Disponibilidad(profesional_id=p.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(12))); db.commit()
    assert client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=payload(s)).status_code==201
    db.close()

def test_reutiliza_por_dni_y_no_sobrescribe_maestro(client):
    db=SessionTest(); p,s=escenario(db); existente=Paciente(nombre="Original",apellido="Paciente",email="old@example.com",dni="12345678",activo=True); db.add(existente); db.flush(); db.add(ProfesionalPaciente(profesional_id=p.id,paciente_id=existente.id)); db.add(Disponibilidad(profesional_id=p.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(12))); db.commit()
    data=payload(s,dni=" 12345678 "); data["fecha_hora"]="2026-09-15T10:30:00-03:00"; assert client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=data).status_code==201
    db.refresh(existente); assert existente.nombre=="Original" and db.query(Paciente).count()==1
    db.close()

def test_slot_ocupado_devuelve_409_y_no_deja_paciente_nuevo(client):
    db=SessionTest(); p,s=escenario(db); db.add(Disponibilidad(profesional_id=p.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(12))); db.commit(); assert client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=payload(s)).status_code==201
    antes=db.query(Paciente).count(); segunda=payload(s,email="otro@example.com"); assert client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=segunda).status_code==409; assert db.query(Paciente).count()==antes
    db.close()

@pytest.mark.parametrize("cambio", ["inactivo", "despublicado", "prestacion_inactiva", "prestacion_no_habilitada"])
def test_publicacion_invalida_404_y_sin_efectos_secundarios(client, cambio):
    db=SessionTest(); p,s=escenario(db)
    if cambio == "inactivo": p.activo=False
    elif cambio == "despublicado": p.reserva_online_activa=False
    elif cambio == "prestacion_inactiva": s.activa=False
    else: s.habilitada_online=False
    db.commit(); antes=(db.query(Paciente).count(),db.query(ProfesionalPaciente).count(),db.query(Turno).count())
    assert client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=payload(s)).status_code==404
    assert (db.query(Paciente).count(),db.query(ProfesionalPaciente).count(),db.query(Turno).count())==antes; db.close()

def test_anticipacion_exacta_permitida_y_una_minuto_menor_rechazada(client, monkeypatch):
    db=SessionTest(); p,s=escenario(db); ahora=datetime(2026,9,15,8,tzinfo=ZONA); monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda:ahora)
    db.add(Disponibilidad(profesional_id=p.id,dia_semana=1,hora_inicio=time(9),hora_fin=time(11))); db.commit()
    body=payload(s); body["fecha_hora"]="2026-09-15T10:00:00-03:00"; assert client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=body).status_code==201
    body["fecha_hora"]="2026-09-15T09:59:00-03:00"; assert client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=body).status_code in (400,409); db.close()

def test_mas_de_60_dias_rechaza_sin_efectos(client, monkeypatch):
    db=SessionTest(); p,s=escenario(db); monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda:datetime(2026,9,15,8,tzinfo=ZONA)); body=payload(s); body["fecha_hora"]="2026-11-15T10:00:00-03:00"; antes=db.query(Paciente).count(); assert client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=body).status_code==400; assert db.query(Paciente).count()==antes; db.close()

def test_franja_extraordinaria_permite_reserva(client, monkeypatch):
    db=SessionTest(); p,s=escenario(db); monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda:datetime(2026,9,15,8,tzinfo=ZONA)); fecha=date(2026,9,18)
    db.add(DisponibilidadExcepcion(profesional_id=p.id,fecha=fecha,tipo="franja_extraordinaria",origen="manual",hora_inicio=time(10),hora_fin=time(11),activa=True)); db.commit(); body=payload(s); body["fecha_hora"]="2026-09-18T10:00:00-03:00"; assert client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=body).status_code==201; db.close()

def test_cierre_de_dia_bloquea_disponibilidad_habitual(client, monkeypatch):
    db=SessionTest(); p,s=escenario(db); monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda:datetime(2026,9,15,8,tzinfo=ZONA)); fecha=date(2026,9,18)
    db.add(Disponibilidad(profesional_id=p.id,dia_semana=4,hora_inicio=time(10),hora_fin=time(11))); db.add(DisponibilidadExcepcion(profesional_id=p.id,fecha=fecha,tipo="cierre_dia",origen="manual",activa=True)); db.commit(); body=payload(s); body["fecha_hora"]="2026-09-18T10:00:00-03:00"; assert client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=body).status_code in (400,409); db.close()

def test_email_cruzado_no_reutiliza_globalmente(client):
    db=SessionTest(); p,s=escenario(db); otro=Profesional(nombre="Otro",apellido="Profesional",matricula="F112-C",activo=True,reserva_online_activa=True,slug_publico="otro-profesional-f112"); db.add(otro); db.flush(); db.add(ProfesionalEspecialidad(profesional_id=otro.id,especialidad_id=s.especialidad_id)); sb=Prestacion(nombre="Consulta B",duracion_minutos=30,precio=100,modalidad="presencial",profesional_id=otro.id,especialidad_id=s.especialidad_id,activa=True,habilitada_online=True); db.add(sb); db.add(Disponibilidad(profesional_id=otro.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(12))); x=Paciente(nombre="Existente",apellido="A",email="persona@example.com",activo=True); db.add(x); db.flush(); db.add(ProfesionalPaciente(profesional_id=p.id,paciente_id=x.id)); db.commit(); body=payload(sb); body["paciente"]["email"]="persona@example.com"; assert client.post(f"/public/profesionales/{otro.slug_publico}/reservas",json=body).status_code==201; assert db.query(Paciente).count()==2; db.close()

def test_dni_cruzado_reutiliza_y_vincula(client):
    db=SessionTest(); p,s=escenario(db); otro=Profesional(nombre="Otro",apellido="Profesional",matricula="F112-D",activo=True,reserva_online_activa=True,slug_publico="otro-profesional-f112b"); db.add(otro); db.flush(); db.add(ProfesionalEspecialidad(profesional_id=otro.id,especialidad_id=s.especialidad_id)); sb=Prestacion(nombre="Consulta B",duracion_minutos=30,precio=100,modalidad="presencial",profesional_id=otro.id,especialidad_id=s.especialidad_id,activa=True,habilitada_online=True); db.add(sb); db.add(Disponibilidad(profesional_id=otro.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(12))); x=Paciente(nombre="Original",apellido="Paciente",email="old@example.com",dni="99999999",activo=True); db.add(x); db.flush(); db.add(ProfesionalPaciente(profesional_id=p.id,paciente_id=x.id)); db.commit(); body=payload(sb,dni=" 99999999 "); assert client.post(f"/public/profesionales/{otro.slug_publico}/reservas",json=body).status_code==201; assert db.query(Paciente).count()==1 and db.query(ProfesionalPaciente).filter_by(paciente_id=x.id).count()==2 and x.nombre=="Original"; db.close()

def test_vinculo_unico_turno_cancelado_y_uuid_estable(client):
    db=SessionTest(); p,s=escenario(db); db.add(Disponibilidad(profesional_id=p.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(13))); db.commit(); body=payload(s); body["fecha_hora"]="2026-09-15T10:30:00-03:00"; first=client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=body); assert first.status_code==201; rid=first.json()["reserva_id"]; body["fecha_hora"]="2026-09-15T11:30:00-03:00"; second=client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=body); assert second.status_code==201; assert db.query(ProfesionalPaciente).count()==1; turno=db.query(Turno).filter(Turno.identificador_publico==rid).one(); assert UUID(turno.identificador_publico).version==4; assert turno.identificador_publico==rid
    turno.estado="cancelado"; db.commit(); body["fecha_hora"]="2026-09-15T10:30:00-03:00"; assert client.post(f"/public/profesionales/{p.slug_publico}/reservas",json=body).status_code==201; db.close()
