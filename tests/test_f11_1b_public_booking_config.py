from decimal import Decimal
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.core.dependencies import obtener_usuario_actual
from app.core.public_booking import es_slug_publico_valido
from app.main import app
from app.models.especialidad import Especialidad
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.profesional_especialidad import ProfesionalEspecialidad
from app.models.usuario import Usuario
from app.services import public_booking_service
from app.services.public_booking_service import actualizar_configuracion
from app.schemas.public_booking import ReservaOnlineActualizar
from tests.conftest import SessionTest


@pytest.fixture(autouse=True)
def limpiar_override():
    yield
    app.dependency_overrides.pop(obtener_usuario_actual, None)


def escenario(db, *, mismo_nombre=False):
    especialidad = Especialidad(nombre="F11B Clínica", duracion_turno_minutos=30)
    usuario_a = Usuario(nombre="Profesional A", email="f11b-a@example.com", password_hash="hash", rol="profesional", activo=True)
    usuario_b = Usuario(nombre="Profesional B", email="f11b-b@example.com", password_hash="hash", rol="profesional", activo=True)
    nombre = "Laura" if mismo_nombre else "Ana"
    profesional_a = Profesional(nombre=nombre, apellido="Gómez", matricula="F11B-A", usuario=usuario_a)
    profesional_b = Profesional(nombre=nombre, apellido="Gómez", matricula="F11B-B", usuario=usuario_b)
    db.add_all([especialidad, profesional_a, profesional_b]); db.flush()
    db.add_all([ProfesionalEspecialidad(profesional_id=profesional_a.id, especialidad_id=especialidad.id), ProfesionalEspecialidad(profesional_id=profesional_b.id, especialidad_id=especialidad.id)])
    propia = Prestacion(nombre="Consulta propia", duracion_minutos=30, precio=Decimal("100"), modalidad="presencial", profesional_id=profesional_a.id, especialidad_id=especialidad.id)
    ajena = Prestacion(nombre="Consulta ajena", duracion_minutos=30, precio=Decimal("100"), modalidad="presencial", profesional_id=profesional_b.id, especialidad_id=especialidad.id)
    db.add_all([propia, ajena]); db.commit(); db.refresh(profesional_a); db.refresh(profesional_b); db.refresh(propia); db.refresh(ajena)
    return profesional_a, profesional_b, propia, ajena, usuario_a, usuario_b


def autenticar(usuario):
    app.dependency_overrides[obtener_usuario_actual] = lambda: usuario


def test_configuracion_inicial_y_activacion(client):
    db = SessionTest(); profesional, _, propia, _, usuario, _ = escenario(db); autenticar(usuario)
    inicial = client.get("/profesionales/me/reserva-online")
    assert inicial.status_code == 200
    assert inicial.json()["reserva_online_activa"] is False
    assert inicial.json()["slug_publico"] is None and inicial.json()["url_publica"] is None
    assert inicial.json()["prestaciones"][0]["identificador_publico"] == propia.identificador_publico
    assert inicial.json()["prestaciones"][0]["habilitada_online"] is False
    activada = client.patch("/profesionales/me/reserva-online", json={"reserva_online_activa": True})
    assert activada.status_code == 200
    datos = activada.json(); assert es_slug_publico_valido(datos["slug_publico"])
    assert datos["url_publica"].endswith(f"/reservar/{datos['slug_publico']}")
    db.close()


def test_desactivar_reactivar_y_cambiar_nombre_conserva_slug(client):
    db = SessionTest(); profesional, _, _, _, usuario, _ = escenario(db); autenticar(usuario)
    slug = client.patch("/profesionales/me/reserva-online", json={"reserva_online_activa": True}).json()["slug_publico"]
    assert client.patch("/profesionales/me/reserva-online", json={"reserva_online_activa": False}).json()["slug_publico"] == slug
    assert client.patch("/profesionales/me/reserva-online", json={"reserva_online_activa": True}).json()["slug_publico"] == slug
    profesional.nombre = "Otro"; profesional.apellido = "Nombre"; db.commit()
    assert client.get("/profesionales/me/reserva-online").json()["slug_publico"] == slug
    db.close()


def test_prestacion_propia_ajena_inactiva_e_inexistente(client):
    db = SessionTest(); profesional, _, propia, ajena, usuario, _ = escenario(db); autenticar(usuario)
    assert client.patch(f"/prestaciones/{propia.identificador_publico}/reserva-online", json={"habilitada_online": True}).status_code == 200
    assert client.patch(f"/prestaciones/{propia.identificador_publico}/reserva-online", json={"habilitada_online": False}).status_code == 200
    assert client.patch(f"/prestaciones/{ajena.identificador_publico}/reserva-online", json={"habilitada_online": True}).status_code == 404
    propia.activa = False; db.commit()
    assert client.patch(f"/prestaciones/{propia.identificador_publico}/reserva-online", json={"habilitada_online": True}).status_code == 409
    assert client.patch("/prestaciones/inexistente/reserva-online", json={"habilitada_online": True}).status_code == 404
    db.close()


@pytest.mark.parametrize("rol", ["recepcionista", "paciente", "administrador"])
def test_roles_no_profesionales_rechazados(client, rol):
    usuario = Usuario(id=999, nombre=rol, email=f"{rol}@f11b.example", password_hash="hash", rol=rol, activo=True)
    autenticar(usuario)
    assert client.get("/profesionales/me/reserva-online").status_code == 403
    assert client.patch("/profesionales/me/reserva-online", json={"reserva_online_activa": True}).status_code == 403


def test_no_autenticado_rechazado(client):
    assert client.get("/profesionales/me/reserva-online").status_code in {401, 403}
    assert client.patch("/profesionales/me/reserva-online", json={"reserva_online_activa": True}).status_code in {401, 403}
    assert client.patch("/prestaciones/no-existe/reserva-online", json={"habilitada_online": True}).status_code in {401, 403}


def test_profesional_inactivo_rechazado(client):
    db = SessionTest(); profesional, _, _, _, usuario, _ = escenario(db); profesional.activo = False; db.commit(); autenticar(usuario)
    assert client.get("/profesionales/me/reserva-online").status_code == 400
    assert client.patch("/profesionales/me/reserva-online", json={"reserva_online_activa": True}).status_code == 400
    db.close()


def test_schemas_rechazan_campos_de_ownership(client):
    usuario = Usuario(id=999, nombre="Profesional", email="schema@f11b.example", password_hash="hash", rol="profesional", activo=True); autenticar(usuario)
    assert client.patch("/profesionales/me/reserva-online", json={"reserva_online_activa": True, "slug_publico": "hack"}).status_code == 422
    assert client.patch("/profesionales/me/reserva-online", json={"reserva_online_activa": True, "cuenta_id": 1}).status_code == 422
    assert client.patch("/prestaciones/x/reserva-online", json={"habilitada_online": True, "profesional_id": 1}).status_code == 422


def test_dos_profesionales_mismo_nombre_obtienen_slugs_distintos(client):
    db = SessionTest(); a, b, _, _, ua, ub = escenario(db, mismo_nombre=True)
    autenticar(ua); slug_a = client.patch("/profesionales/me/reserva-online", json={"reserva_online_activa": True}).json()["slug_publico"]
    autenticar(ub); slug_b = client.patch("/profesionales/me/reserva-online", json={"reserva_online_activa": True}).json()["slug_publico"]
    assert slug_a != slug_b
    db.close()


def test_slug_extremo_y_uuid_publico():
    db = SessionTest(); a, _, propia, _, _, _ = escenario(db)
    a.nombre = "Á" * 200; a.apellido = "Ñ" * 200; db.commit()
    actualizado = actualizar_configuracion(db, a, ReservaOnlineActualizar(reserva_online_activa=True))
    assert len(actualizado.slug_publico) <= 120 and es_slug_publico_valido(actualizado.slug_publico)
    assert UUID(propia.identificador_publico).version == 4
    db.close()


def test_colision_de_slug_reintenta_y_no_sobrescribe(monkeypatch):
    db = SessionTest(); a, b, _, _, _, _ = escenario(db)
    b.slug_publico = "laura-gomez-de-otro"; db.commit()
    valores = iter(["laura-gomez-de-otro", "laura-gomez-libre"])
    monkeypatch.setattr(public_booking_service, "generar_slug_publico", lambda *_: next(valores))
    resultado = actualizar_configuracion(db, a, ReservaOnlineActualizar(reserva_online_activa=True))
    assert resultado.slug_publico == "laura-gomez-libre"
    assert db.get(Profesional, b.id).slug_publico == "laura-gomez-de-otro"
    db.close()


def test_colision_agotada_devuelve_error_y_no_activa(monkeypatch):
    db = SessionTest(); a, b, _, _, _, _ = escenario(db)
    b.slug_publico = "ocupado"; db.commit()
    monkeypatch.setattr(public_booking_service, "generar_slug_publico", lambda *_: "ocupado")
    with pytest.raises(HTTPException) as error:
        actualizar_configuracion(db, a, ReservaOnlineActualizar(reserva_online_activa=True))
    assert error.value.status_code == 409
    db.expire_all()
    persistido = db.get(Profesional, a.id)
    assert persistido.reserva_online_activa is False and persistido.slug_publico is None
    db.close()
