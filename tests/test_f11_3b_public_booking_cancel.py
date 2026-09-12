from datetime import date, time
import pytest
from tests.conftest import SessionTest
from app.models.disponibilidad import Disponibilidad
from app.models.turno import Turno
from app.core.public_booking import hash_token_autogestion
from tests.test_f11_2_public_booking_create import escenario, payload

def reservar(client, db):
    profesional, prestacion = escenario(db)
    db.add(Disponibilidad(profesional_id=profesional.id, dia_semana=1, hora_inicio=time(10), hora_fin=time(12))); db.commit()
    response = client.post(f"/public/profesionales/{profesional.slug_publico}/reservas", json=payload(prestacion))
    return profesional, prestacion, response.json()

def test_cancelar_reservado_es_idempotente_y_conserva_token(client):
    db=SessionTest(); profesional, prestacion, reserva=reservar(client, db); token=reserva["autogestion_token"]
    response=client.post(f"/public/reservas/{token}/cancelar"); assert response.status_code==200 and response.json()["estado"]=="cancelado"
    segunda=client.post(f"/public/reservas/{token}/cancelar"); assert segunda.status_code==200
    assert client.get(f"/public/reservas/{token}").json()["estado"]=="cancelado"
    turno=db.query(Turno).filter_by(autogestion_token_hash=hash_token_autogestion(token)).one(); assert turno.estado=="cancelado"
    db.close()

def test_cancelar_confirmado(client):
    db=SessionTest(); _, _, reserva=reservar(client, db); token=reserva["autogestion_token"]
    turno=db.query(Turno).filter_by(autogestion_token_hash=hash_token_autogestion(token)).one(); turno.estado="confirmado"; db.commit()
    response=client.post(f"/public/reservas/{token}/cancelar")
    assert response.status_code==200 and response.json()["estado"]=="cancelado"
    db.close()

@pytest.mark.parametrize("estado", ["finalizado", "ausente"])
def test_estados_no_cancelables_rechazados(client, estado):
    db=SessionTest(); _, _, reserva=reservar(client, db); turno=db.query(Turno).filter_by(autogestion_token_hash=hash_token_autogestion(reserva["autogestion_token"])).one(); turno.estado=estado; db.commit()
    assert client.post(f"/public/reservas/{reserva['autogestion_token']}/cancelar").status_code==409
    db.close()

def test_token_invalido_no_revela_reserva(client):
    assert client.post("/public/reservas/no-existe/cancelar").status_code==404

@pytest.mark.parametrize("token", ["", "x" * 513, "token-alterado"])
def test_tokens_invalidos_rechazo_controlado(client, token):
    if token == "":
        assert client.post("/public/reservas//cancelar").status_code in (404, 405)
    else:
        assert client.post(f"/public/reservas/{token}/cancelar").status_code in (404, 422)

@pytest.mark.parametrize("estado", ["finalizado", "ausente"])
def test_cancelacion_no_cambia_invariantes_en_estado_no_cancelable(client, estado):
    db=SessionTest(); _, _, reserva=reservar(client, db); token=reserva["autogestion_token"]
    turno=db.query(Turno).filter_by(autogestion_token_hash=hash_token_autogestion(token)).one()
    invariantes=(turno.id, turno.identificador_publico, turno.autogestion_token_hash, turno.fecha_hora, turno.fecha_fin, turno.paciente_id, turno.profesional_id, turno.prestacion_id)
    turno.estado=estado; db.commit()
    assert client.post(f"/public/reservas/{token}/cancelar").status_code==409
    db.refresh(turno)
    assert (turno.id, turno.identificador_publico, turno.autogestion_token_hash, turno.fecha_hora, turno.fecha_fin, turno.paciente_id, turno.profesional_id, turno.prestacion_id)==invariantes
    db.close()

def test_respuesta_segura_y_headers_privados(client):
    db=SessionTest(); _, _, reserva=reservar(client, db); token=reserva["autogestion_token"]
    response=client.post(f"/public/reservas/{token}/cancelar")
    assert response.headers["cache-control"]=="no-store" and response.headers["referrer-policy"]=="no-referrer"
    assert "location" not in response.headers
    data=response.json()
    for campo in ("autogestion_token", "autogestion_token_hash", "paciente_id", "profesional_id", "prestacion_id", "cuenta_id", "usuario_id", "dni", "email", "telefono", "matricula", "observaciones", "historia_clinica", "paciente"):
        assert campo not in data
    assert {"reserva_id", "estado", "fecha_hora", "fecha_fin", "profesional", "prestacion"} <= set(data)
    assert data["fecha_hora"].endswith(("-03:00", "+00:00")) and data["fecha_fin"].endswith(("-03:00", "+00:00"))
    db.close()

def test_cancelacion_no_elimina_turno_y_get_posterior_mantiene_estado(client):
    db=SessionTest(); _, _, reserva=reservar(client, db); token=reserva["autogestion_token"]
    turno=db.query(Turno).filter_by(autogestion_token_hash=hash_token_autogestion(token)).one(); snapshot=(turno.id, turno.identificador_publico, turno.autogestion_token_hash, turno.fecha_hora, turno.fecha_fin)
    assert client.post(f"/public/reservas/{token}/cancelar").status_code==200
    db.refresh(turno); assert (turno.id, turno.identificador_publico, turno.autogestion_token_hash, turno.fecha_hora, turno.fecha_fin)==snapshot
    assert client.get(f"/public/reservas/{token}").json()["estado"]=="cancelado"
    db.close()

def test_rate_limit_cancelacion_es_independiente_de_consulta(client):
    db=SessionTest(); _, _, reserva=reservar(client, db); token=reserva["autogestion_token"]
    for _ in range(10): assert client.post(f"/public/reservas/{token}/cancelar").status_code==200
    assert client.post(f"/public/reservas/{token}/cancelar").status_code==429
    assert client.get(f"/public/reservas/{token}").status_code==200
    db.close()

def test_cancelacion_libera_slot_y_permite_segunda_reserva(client, monkeypatch):
    db=SessionTest(); profesional, prestacion=escenario(db)
    monkeypatch.setattr("app.services.public_booking_service.ahora_negocio", lambda: __import__('datetime').datetime(2026, 9, 15, 8, tzinfo=__import__('zoneinfo').ZoneInfo("America/Argentina/Buenos_Aires")))
    db.add(Disponibilidad(profesional_id=profesional.id, dia_semana=1, hora_inicio=time(10), hora_fin=time(10,30))); db.commit()
    body=payload(prestacion); body["fecha_hora"]="2026-09-15T10:00:00-03:00"
    first=client.post(f"/public/profesionales/{profesional.slug_publico}/reservas", json=body); assert first.status_code==201
    token=first.json()["autogestion_token"]
    params={"prestacion":prestacion.identificador_publico,"fecha_desde":"2026-09-15","fecha_hasta":"2026-09-15"}
    assert client.get(f"/public/profesionales/{profesional.slug_publico}/disponibilidad", params=params).json()["dias"][0]["horarios"]==[]
    assert client.post(f"/public/reservas/{token}/cancelar").status_code==200
    horarios=client.get(f"/public/profesionales/{profesional.slug_publico}/disponibilidad", params=params).json()["dias"][0]["horarios"]
    assert horarios==["2026-09-15T10:00:00-03:00"]
    second_body=payload(prestacion,email="segunda@example.com"); second_body["fecha_hora"]="2026-09-15T10:00:00-03:00"
    second=client.post(f"/public/profesionales/{profesional.slug_publico}/reservas", json=second_body); assert second.status_code==201
    assert second.json()["reserva_id"] != first.json()["reserva_id"]
    first_turno=db.query(Turno).filter_by(identificador_publico=first.json()["reserva_id"]).one(); second_turno=db.query(Turno).filter_by(identificador_publico=second.json()["reserva_id"]).one()
    assert first_turno.estado=="cancelado" and second_turno.estado=="reservado" and first_turno.autogestion_token_hash != second_turno.autogestion_token_hash
    db.close()

def test_bucket_cancelacion_no_bloquea_creacion(client):
    db=SessionTest(); profesional, prestacion, first=reservar(client, db)
    token=first["autogestion_token"]
    for _ in range(10): assert client.post(f"/public/reservas/{token}/cancelar").status_code==200
    assert client.post(f"/public/reservas/{token}/cancelar").status_code==429
    body=payload(prestacion,email="otro-bucket@example.com"); body["fecha_hora"]="2026-09-15T11:00:00-03:00"
    assert client.post(f"/public/profesionales/{profesional.slug_publico}/reservas", json=body).status_code==201
    db.close()

def test_cancelacion_normaliza_sqlite_naive(client):
    db=SessionTest(); _, _, reserva=reservar(client, db); token=reserva["autogestion_token"]
    turno=db.query(Turno).filter_by(autogestion_token_hash=hash_token_autogestion(token)).one()
    turno.fecha_hora=turno.fecha_hora.replace(tzinfo=None); turno.fecha_fin=turno.fecha_fin.replace(tzinfo=None); db.commit()
    response=client.post(f"/public/reservas/{token}/cancelar"); assert response.status_code==200
    assert response.json()["fecha_hora"].endswith(("-03:00", "+00:00")) and response.json()["fecha_fin"].endswith(("-03:00", "+00:00"))
    db.close()
