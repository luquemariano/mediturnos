from datetime import date, datetime, time
from zoneinfo import ZoneInfo
import pytest
from tests.conftest import SessionTest
from app.models.disponibilidad import Disponibilidad
from app.models.disponibilidad_excepcion import DisponibilidadExcepcion
from app.models.turno import Turno
from app.core.public_booking import hash_token_autogestion
from tests.test_f11_2_public_booking_create import escenario, payload

ZONA=ZoneInfo("America/Argentina/Buenos_Aires")

def preparar(client):
    db=SessionTest(); profesional, prestacion=escenario(db)
    db.add(Disponibilidad(profesional_id=profesional.id,dia_semana=1,hora_inicio=time(10),hora_fin=time(12))); db.commit()
    body=payload(prestacion); body["fecha_hora"]="2026-09-15T10:00:00-03:00"
    reserva=client.post(f"/public/profesionales/{profesional.slug_publico}/reservas",json=body).json()
    return db, profesional, prestacion, reserva

def test_reprogramar_reservado_conserva_identidad_y_token(client, monkeypatch):
    monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda: datetime(2026,9,15,8,tzinfo=ZONA))
    db, profesional, prestacion, reserva=preparar(client); token=reserva["autogestion_token"]
    turno=db.query(Turno).filter_by(autogestion_token_hash=hash_token_autogestion(token)).one(); original=(turno.id,turno.identificador_publico,turno.autogestion_token_hash,turno.paciente_id,turno.profesional_id,turno.prestacion_id)
    response=client.post(f"/public/reservas/{token}/reprogramar",json={"fecha_hora":"2026-09-15T11:00:00-03:00"})
    assert response.status_code==200 and response.json()["estado"]=="reservado" and response.headers["cache-control"]=="no-store"
    db.refresh(turno); assert (turno.id,turno.identificador_publico,turno.autogestion_token_hash,turno.paciente_id,turno.profesional_id,turno.prestacion_id)==original
    assert turno.fecha_hora != turno.fecha_fin and client.get(f"/public/reservas/{token}").json()["fecha_hora"]=="2026-09-15T11:00:00-03:00"
    db.close()

def test_reprogramar_confirmado_conserva_estado_identidad(client, monkeypatch):
    monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda: datetime(2026,9,15,8,tzinfo=ZONA))
    db, _, _, reserva=preparar(client); token=reserva["autogestion_token"]; turno=db.query(Turno).filter_by(autogestion_token_hash=hash_token_autogestion(token)).one(); turno.estado="confirmado"; db.commit()
    response=client.post(f"/public/reservas/{token}/reprogramar",json={"fecha_hora":"2026-09-15T11:00:00-03:00"})
    assert response.status_code==200 and response.json()["estado"]=="confirmado"; db.refresh(turno); assert turno.estado=="confirmado"; db.close()

@pytest.mark.parametrize("fecha,esperado",[("2026-09-15T10:00:00-03:00",200),("2026-09-15T09:59:00-03:00",400),("2026-11-14T10:00:00-03:00",400)])
def test_politica_temporal_publica(client, monkeypatch, fecha, esperado):
    ahora=datetime(2026,9,15,8,tzinfo=ZONA); monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda: ahora)
    db, _, _, reserva=preparar(client); response=client.post(f"/public/reservas/{reserva['autogestion_token']}/reprogramar",json={"fecha_hora":fecha}); assert response.status_code==esperado; db.close()

def test_datetime_naive_es_rechazado(client):
    db, _, _, reserva=preparar(client); assert client.post(f"/public/reservas/{reserva['autogestion_token']}/reprogramar",json={"fecha_hora":"2026-09-15T11:00:00"}).status_code==422; db.close()

def test_conflicto_no_muta_turno_original(client, monkeypatch):
    monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda: datetime(2026,9,15,8,tzinfo=ZONA))
    db, profesional, prestacion, reserva=preparar(client); token=reserva["autogestion_token"]; turno=db.query(Turno).filter_by(autogestion_token_hash=hash_token_autogestion(token)).one()
    otro_body=payload(prestacion,email="ocupante@example.com"); otro_body["fecha_hora"]="2026-09-15T11:00:00-03:00"; assert client.post(f"/public/profesionales/{profesional.slug_publico}/reservas",json=otro_body).status_code==201
    original=(turno.fecha_hora,turno.fecha_fin,turno.estado,turno.identificador_publico,turno.autogestion_token_hash)
    assert client.post(f"/public/reservas/{token}/reprogramar",json={"fecha_hora":"2026-09-15T11:00:00-03:00"}).status_code==409
    db.refresh(turno); assert (turno.fecha_hora,turno.fecha_fin,turno.estado,turno.identificador_publico,turno.autogestion_token_hash)==original; db.close()

def test_disponibilidad_antes_y_despues_de_reprogramar(client, monkeypatch):
    monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda: datetime(2026,9,15,8,tzinfo=ZONA))
    db, profesional, prestacion, reserva=preparar(client); token=reserva["autogestion_token"]
    params={"prestacion":prestacion.identificador_publico,"fecha_desde":"2026-09-15","fecha_hasta":"2026-09-15"}
    before=client.get(f"/public/profesionales/{profesional.slug_publico}/disponibilidad",params=params).json()["dias"][0]["horarios"]
    assert "2026-09-15T10:00:00-03:00" not in before and "2026-09-15T10:30:00-03:00" in before
    assert client.post(f"/public/reservas/{token}/reprogramar",json={"fecha_hora":"2026-09-15T10:30:00-03:00"}).status_code==200
    after=client.get(f"/public/profesionales/{profesional.slug_publico}/disponibilidad",params=params).json()["dias"][0]["horarios"]
    assert "2026-09-15T10:00:00-03:00" in after and "2026-09-15T10:30:00-03:00" not in after
    db.close()

def test_doble_reprogramacion_y_duracion(client, monkeypatch):
    monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda: datetime(2026,9,15,8,tzinfo=ZONA))
    db, _, prestacion, reserva=preparar(client); token=reserva["autogestion_token"]
    for hora in ("2026-09-15T10:30:00-03:00","2026-09-15T11:00:00-03:00"):
        assert client.post(f"/public/reservas/{token}/reprogramar",json={"fecha_hora":hora}).status_code==200
    data=client.get(f"/public/reservas/{token}").json(); assert data["fecha_hora"]=="2026-09-15T11:00:00-03:00" and data["fecha_fin"]=="2026-09-15T11:30:00-03:00"; db.close()

def test_misma_fecha_hora_es_idempotente(client, monkeypatch):
    monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda: datetime(2026,9,15,8,tzinfo=ZONA))
    db, _, _, reserva=preparar(client); token=reserva["autogestion_token"]
    response=client.post(f"/public/reservas/{token}/reprogramar",json={"fecha_hora":"2026-09-15T10:00:00-03:00"})
    assert response.status_code==200 and response.json()["fecha_hora"]=="2026-09-15T10:00:00-03:00"; db.close()

def test_cierre_de_dia_rechaza_sin_mutar(client, monkeypatch):
    monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda: datetime(2026,9,15,8,tzinfo=ZONA))
    db, profesional, _, reserva=preparar(client); token=reserva["autogestion_token"]; turno=db.query(Turno).filter_by(autogestion_token_hash=hash_token_autogestion(token)).one(); original=turno.fecha_hora
    db.add(DisponibilidadExcepcion(profesional_id=profesional.id,fecha=date(2026,9,15),tipo="cierre_dia",origen="manual",activa=True)); db.commit()
    assert client.post(f"/public/reservas/{token}/reprogramar",json={"fecha_hora":"2026-09-15T11:00:00-03:00"}).status_code in (400,409); db.refresh(turno); assert turno.fecha_hora==original; db.close()

def test_franja_extraordinaria_permite_reprogramar(client, monkeypatch):
    monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda: datetime(2026,9,15,8,tzinfo=ZONA))
    db, profesional, _, reserva=preparar(client); token=reserva["autogestion_token"]
    db.add(DisponibilidadExcepcion(profesional_id=profesional.id,fecha=date(2026,9,15),tipo="franja_extraordinaria",origen="manual",hora_inicio=time(12),hora_fin=time(13),activa=True)); db.commit()
    assert client.post(f"/public/reservas/{token}/reprogramar",json={"fecha_hora":"2026-09-15T12:00:00-03:00"}).status_code==200; db.close()

def test_sqlite_naive_y_privacidad(client, monkeypatch):
    monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda: datetime(2026,9,15,8,tzinfo=ZONA))
    db, _, _, reserva=preparar(client); token=reserva["autogestion_token"]; turno=db.query(Turno).filter_by(autogestion_token_hash=hash_token_autogestion(token)).one(); turno.fecha_hora=turno.fecha_hora.replace(tzinfo=None); turno.fecha_fin=turno.fecha_fin.replace(tzinfo=None); db.commit()
    response=client.post(f"/public/reservas/{token}/reprogramar",json={"fecha_hora":"2026-09-15T11:00:00-03:00"}); assert response.status_code==200; assert response.headers["cache-control"]=="no-store" and response.headers["referrer-policy"]=="no-referrer"; assert "autogestion_token" not in response.json(); db.close()

def test_rate_limit_reprogramacion_10_11_y_buckets_independientes(client, monkeypatch):
    monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda: datetime(2026,9,15,8,tzinfo=ZONA))
    db, profesional, prestacion, reserva=preparar(client); token=reserva["autogestion_token"]
    for _ in range(10):
        response=client.post(f"/public/reservas/{token}/reprogramar",json={"fecha_hora":"2026-09-15T10:00:00-03:00"})
        assert response.status_code==200
    assert client.post(f"/public/reservas/{token}/reprogramar",json={"fecha_hora":"2026-09-15T10:00:00-03:00"}).status_code==429
    assert client.get(f"/public/reservas/{token}").status_code==200
    assert client.post(f"/public/reservas/{token}/cancelar").status_code==200
    body=payload(prestacion,email="bucket-independiente@example.com"); body["fecha_hora"]="2026-09-15T11:00:00-03:00"
    assert client.post(f"/public/profesionales/{profesional.slug_publico}/reservas",json=body).status_code==201
    db.close()

def test_invariantes_completas_exitosas_y_duracion(client, monkeypatch):
    monkeypatch.setattr("app.services.public_booking_service.ahora_negocio",lambda: datetime(2026,9,15,8,tzinfo=ZONA))
    db, _, prestacion, reserva=preparar(client); token=reserva["autogestion_token"]; turno=db.query(Turno).filter_by(autogestion_token_hash=hash_token_autogestion(token)).one()
    before=(turno.id,turno.identificador_publico,turno.autogestion_token_hash,turno.paciente_id,turno.profesional_id,turno.prestacion_id,turno.estado,turno.fecha_hora,turno.fecha_fin)
    assert client.post(f"/public/reservas/{token}/reprogramar",json={"fecha_hora":"2026-09-15T11:00:00-03:00"}).status_code==200; db.refresh(turno)
    after=(turno.id,turno.identificador_publico,turno.autogestion_token_hash,turno.paciente_id,turno.profesional_id,turno.prestacion_id,turno.estado,turno.fecha_hora,turno.fecha_fin)
    assert after[:7]==before[:7] and after[7]!=before[7] and after[8]!=before[8]
    assert (turno.fecha_fin-turno.fecha_hora).total_seconds()==prestacion.duracion_minutos*60; db.close()

@pytest.mark.parametrize("campo",["profesional_id","prestacion_id","paciente_id","fecha_fin","estado","reserva_id","identificador_publico","autogestion_token"])
def test_payload_extra_rechazado(client, campo):
    db, _, _, reserva=preparar(client); payload_extra={"fecha_hora":"2026-09-15T11:00:00-03:00",campo:1}; assert client.post(f"/public/reservas/{reserva['autogestion_token']}/reprogramar",json=payload_extra).status_code==422; db.close()

@pytest.mark.parametrize("estado",["cancelado","finalizado","ausente"])
def test_estados_no_reprogramables(client, estado):
    db, _, _, reserva=preparar(client); token=reserva["autogestion_token"]
    turno=db.query(Turno).filter_by(autogestion_token_hash=hash_token_autogestion(token)).one(); turno.estado=estado; db.commit()
    assert client.post(f"/public/reservas/{token}/reprogramar",json={"fecha_hora":"2026-09-15T11:00:00-03:00"}).status_code in (400,409)
    db.close()

def test_reprogramar_token_invalido_y_payload_extra(client):
    assert client.post("/public/reservas/no-existe/reprogramar",json={"fecha_hora":"2026-09-15T11:00:00-03:00"}).status_code==404
    db, profesional, prestacion, reserva=preparar(client)
    assert client.post(f"/public/reservas/{reserva['autogestion_token']}/reprogramar",json={"fecha_hora":"2026-09-15T11:00:00-03:00","estado":"cancelado"}).status_code==422
    db.close()
