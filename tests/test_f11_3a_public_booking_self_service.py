from datetime import datetime, time
import hashlib
import pytest
from tests.conftest import SessionTest
from app.models.disponibilidad import Disponibilidad
from app.models.turno import Turno
from app.core.public_booking import hash_token_autogestion, generar_token_autogestion
from tests.test_f11_2_public_booking_create import escenario, payload


def test_creacion_entrega_token_y_consulta_publica_segura(client):
    db = SessionTest(); profesional, prestacion = escenario(db)
    db.add(Disponibilidad(profesional_id=profesional.id, dia_semana=1, hora_inicio=time(10), hora_fin=time(12))); db.commit()
    response = client.post(f"/public/profesionales/{profesional.slug_publico}/reservas", json=payload(prestacion))
    assert response.status_code == 201
    data = response.json(); token = data["autogestion_token"]
    turno = db.query(Turno).filter_by(identificador_publico=data["reserva_id"]).one()
    assert token and token != data["reserva_id"] and turno.autogestion_token_hash == hash_token_autogestion(token) and token not in turno.autogestion_token_hash
    consulta = client.get(f"/public/reservas/{token}")
    assert consulta.status_code == 200 and consulta.json()["estado"] == "reservado"
    assert "autogestion_token" not in consulta.json() and "autogestion_token_hash" not in consulta.json()
    assert "paciente" not in consulta.json() and consulta.json()["fecha_hora"].endswith("-03:00")
    assert client.get(f"/public/reservas/{token[:-1]}x").status_code == 404
    assert client.get(f"/public/reservas/{data['reserva_id']}").status_code == 404
    db.close()


def test_turno_historico_sin_token_no_es_consultable(client):
    db = SessionTest(); profesional, prestacion = escenario(db)
    from app.models.paciente import Paciente
    paciente = Paciente(nombre="Histórico", apellido="Paciente", email="historico@example.com", activo=True)
    db.add(paciente); db.flush()
    turno = Turno(paciente_id=paciente.id, prestacion_id=prestacion.id, profesional_id=profesional.id, fecha_hora=__import__('datetime').datetime(2026, 9, 15, 13), fecha_fin=__import__('datetime').datetime(2026, 9, 15, 13, 30))
    db.add(turno); db.commit()
    assert client.get(f"/public/reservas/{turno.identificador_publico}").status_code == 404
    db.close()


def test_helpers_generan_tokens_distintos():
    assert generar_token_autogestion() != generar_token_autogestion()


def test_helpers_sha256_estable_y_hexadecimal():
    token = generar_token_autogestion()
    assert hash_token_autogestion(token) == hash_token_autogestion(token)
    assert hash_token_autogestion(token) == hashlib.sha256(token.encode()).hexdigest()
    assert len(hash_token_autogestion(token)) == 64
    assert hash_token_autogestion(token) != hash_token_autogestion(generar_token_autogestion())


@pytest.mark.parametrize("estado", ["reservado", "confirmado", "cancelado", "finalizado", "ausente"])
def test_todos_los_estados_son_consultables(client, estado):
    db = SessionTest(); profesional, prestacion = escenario(db)
    db.add(Disponibilidad(profesional_id=profesional.id, dia_semana=1, hora_inicio=time(10), hora_fin=time(12))); db.commit()
    response = client.post(f"/public/profesionales/{profesional.slug_publico}/reservas", json=payload(prestacion))
    token = response.json()["autogestion_token"]
    turno = db.query(Turno).filter_by(autogestion_token_hash=hash_token_autogestion(token)).one(); turno.estado = estado; db.commit()
    assert client.get(f"/public/reservas/{token}").json()["estado"] == estado
    db.close()


def test_token_vacio_largo_y_reserva_id_rechazados(client):
    assert client.get("/public/reservas/").status_code in (404, 405)
    assert client.get("/public/reservas/" + "x" * 513).status_code in (404, 422)
    db = SessionTest(); profesional, prestacion = escenario(db)
    db.add(Disponibilidad(profesional_id=profesional.id, dia_semana=1, hora_inicio=time(10), hora_fin=time(12))); db.commit()
    response = client.post(f"/public/profesionales/{profesional.slug_publico}/reservas", json=payload(prestacion))
    assert client.get(f"/public/reservas/{response.json()['reserva_id']}").status_code == 404
    db.close()


def test_respuesta_publica_no_expone_datos_sensibles(client):
    db = SessionTest(); profesional, prestacion = escenario(db)
    db.add(Disponibilidad(profesional_id=profesional.id, dia_semana=1, hora_inicio=time(10), hora_fin=time(12))); db.commit()
    token = client.post(f"/public/profesionales/{profesional.slug_publico}/reservas", json=payload(prestacion)).json()["autogestion_token"]
    data = client.get(f"/public/reservas/{token}").json()
    assert set(data) == {"reserva_id", "estado", "fecha_hora", "fecha_fin", "zona_horaria", "profesional_slug", "prestacion_identificador_publico", "profesional", "prestacion"}
    assert data["profesional"] == {"nombre": profesional.nombre, "apellido": profesional.apellido}
    assert data["prestacion"] == {"nombre": prestacion.nombre, "modalidad": prestacion.modalidad}
    assert data["fecha_hora"].endswith("-03:00") and data["fecha_fin"].endswith("-03:00")
    db.close()
