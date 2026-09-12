from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
import pytest
from tests.conftest import SessionTest
from app.models.disponibilidad import Disponibilidad
from app.models.turno import Turno
from app.models.paciente import Paciente
from app.models.profesional_paciente import ProfesionalPaciente
from app.services.email_service import construir_email_confirmacion_reserva_publica, EmailDeliveryError
from app.core.config import settings
from app.services.email_service import development_email_outbox
from tests.test_f11_2_public_booking_create import escenario, payload
import pytest

def test_reserva_publica_envia_confirmacion_con_mismo_token(client):
    development_email_outbox.clear(); db=SessionTest(); profesional, prestacion=escenario(db)
    db.add(Disponibilidad(profesional_id=profesional.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(12))); db.commit()
    response=client.post(f"/public/profesionales/{profesional.slug_publico}/reservas",json=payload(prestacion)); assert response.status_code==201
    reserva=response.json(); contenido=development_email_outbox["ana@example.com"]
    assert "Tu turno fue reservado - Turnelia" not in contenido
    assert "Turnelia" in contenido and "Laura Gómez" in contenido and "Consulta" in contenido and "presencial" in contenido
    assert f"/reserva/{reserva['autogestion_token']}" in contenido
    assert reserva["autogestion_token"] in contenido and "autogestion_token_hash" not in contenido
    for campo in ("profesional_id", "prestacion_id", "paciente_id", "cuenta_id", "usuario_id"):
        assert campo not in contenido
    db.close()

def test_email_subject_html_text_y_frontend_url_sin_doble_slash():
    mensaje=construir_email_confirmacion_reserva_publica(destinatario="ana@example.com",paciente="Ana Pérez",profesional="Laura Gómez",prestacion="Consulta",modalidad="presencial",fecha_hora=__import__('datetime').datetime(2026,9,15,13,30,tzinfo=__import__('datetime').timezone.utc),autogestion_token="tok")
    assert mensaje.asunto=="Tu turno fue reservado - Turnelia"; assert "10:30 hs" in mensaje.texto and "/reserva/tok" in mensaje.texto; assert "10:30" in mensaje.html and "tok" in mensaje.html

def test_fallo_email_conserva_turno_hash_y_uuid(client, monkeypatch):
    db=SessionTest(); profesional, prestacion=escenario(db); db.add(Disponibilidad(profesional_id=profesional.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(12))); db.commit()
    monkeypatch.setattr("app.services.public_booking_service.enviar_confirmacion_reserva_publica", lambda **kwargs: (_ for _ in ()).throw(EmailDeliveryError("fallo")))
    response=client.post(f"/public/profesionales/{profesional.slug_publico}/reservas",json=payload(prestacion)); assert response.status_code==201
    turno=db.query(Turno).filter_by(identificador_publico=response.json()["reserva_id"]).one(); assert turno.autogestion_token_hash and turno.identificador_publico==response.json()["reserva_id"] and turno.estado=="reservado"; db.close()

def test_slot_ocupado_no_envia_email(client, monkeypatch):
    db=SessionTest(); profesional, prestacion=escenario(db); db.add(Disponibilidad(profesional_id=profesional.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(12))); db.commit()
    first=client.post(f"/public/profesionales/{profesional.slug_publico}/reservas",json=payload(prestacion)); calls=[]; monkeypatch.setattr("app.services.public_booking_service.enviar_confirmacion_reserva_publica",lambda **kwargs:calls.append(kwargs))
    second=client.post(f"/public/profesionales/{profesional.slug_publico}/reservas",json=payload(prestacion,email="otro@example.com")); assert second.status_code==409 and calls==[]; db.close()

@pytest.mark.parametrize("modo",["inactivo","despublicado","prestacion_inactiva","no_habilitada"])
def test_publicacion_invalida_no_envia_email(client, monkeypatch, modo):
    db=SessionTest(); profesional, prestacion=escenario(db)
    if modo=="inactivo": profesional.activo=False
    elif modo=="despublicado": profesional.reserva_online_activa=False
    elif modo=="prestacion_inactiva": prestacion.activa=False
    else: prestacion.habilitada_online=False
    db.commit(); calls=[]; monkeypatch.setattr("app.services.public_booking_service.enviar_confirmacion_reserva_publica",lambda **kwargs:calls.append(kwargs))
    assert client.post(f"/public/profesionales/{profesional.slug_publico}/reservas",json=payload(prestacion)).status_code==404 and calls==[]; db.close()

def test_paciente_reutilizado_por_dni_usa_email_actual_sin_sobrescribir_maestro(client, monkeypatch):
    db=SessionTest(); profesional, prestacion=escenario(db); maestro=Paciente(nombre="Maestro",apellido="Original",email="maestro@example.com",dni="123",activo=True); db.add(maestro); db.flush(); db.add(ProfesionalPaciente(profesional_id=profesional.id,paciente_id=maestro.id)); db.add(Disponibilidad(profesional_id=profesional.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(12))); db.commit()
    calls=[]; monkeypatch.setattr("app.services.public_booking_service.enviar_confirmacion_reserva_publica",lambda **kwargs:calls.append(kwargs)); body=payload(prestacion,dni="123",email="contacto@example.com")
    assert client.post(f"/public/profesionales/{profesional.slug_publico}/reservas",json=body).status_code==201
    db.refresh(maestro); assert maestro.email=="maestro@example.com" and len(calls)==1 and calls[0]["destinatario"]=="contacto@example.com"; db.close()

def test_validacion_temporal_invalida_no_intenta_email(client, monkeypatch):
    db=SessionTest(); profesional, prestacion=escenario(db); db.add(Disponibilidad(profesional_id=profesional.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(12))); db.commit(); calls=[]
    monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda: datetime(2026,9,15,8,tzinfo=ZoneInfo("America/Argentina/Buenos_Aires"))); monkeypatch.setattr("app.services.public_booking_service.enviar_confirmacion_reserva_publica",lambda **kwargs:calls.append(kwargs)); body=payload(prestacion); body["fecha_hora"]="2026-09-15T09:59:00-03:00"
    assert client.post(f"/public/profesionales/{profesional.slug_publico}/reservas",json=body).status_code==400 and calls==[]; db.close()

def test_timezone_end_to_end_en_html_y_texto(client):
    development_email_outbox.clear(); db=SessionTest(); profesional, prestacion=escenario(db); db.add(Disponibilidad(profesional_id=profesional.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(12))); db.commit(); body=payload(prestacion); body["fecha_hora"]="2026-09-15T10:30:00-03:00"
    response=client.post(f"/public/profesionales/{profesional.slug_publico}/reservas",json=body); assert response.status_code==201; contenido=development_email_outbox["ana@example.com"]; assert "10:30 hs" in contenido and "13:30" not in contenido; db.close()

def test_envio_exacto_una_vez(client, monkeypatch):
    db=SessionTest(); profesional, prestacion=escenario(db); db.add(Disponibilidad(profesional_id=profesional.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(12))); db.commit(); calls=[]; monkeypatch.setattr("app.services.public_booking_service.enviar_confirmacion_reserva_publica",lambda **kwargs:calls.append(kwargs)); assert client.post(f"/public/profesionales/{profesional.slug_publico}/reservas",json=payload(prestacion)).status_code==201; assert len(calls)==1; db.close()

def test_fallo_email_no_loggea_token(client, monkeypatch, caplog):
    db=SessionTest(); profesional, prestacion=escenario(db); db.add(Disponibilidad(profesional_id=profesional.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(12))); db.commit()
    monkeypatch.setattr("app.services.public_booking_service.enviar_confirmacion_reserva_publica",lambda **kwargs: (_ for _ in ()).throw(RuntimeError("fallo"))); response=client.post(f"/public/profesionales/{profesional.slug_publico}/reservas",json=payload(prestacion)); token=response.json()["autogestion_token"]
    assert response.status_code==201 and token not in caplog.text; db.close()

def test_fallo_email_no_revierte_reserva(client, monkeypatch):
    db=SessionTest(); profesional, prestacion=escenario(db); db.add(Disponibilidad(profesional_id=profesional.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(12))); db.commit()
    monkeypatch.setattr("app.services.public_booking_service.enviar_confirmacion_reserva_publica", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("fallo")))
    response=client.post(f"/public/profesionales/{profesional.slug_publico}/reservas",json=payload(prestacion)); assert response.status_code==201
    assert db.query(__import__('app.models.turno',fromlist=['Turno']).Turno).count()==1; db.close()
