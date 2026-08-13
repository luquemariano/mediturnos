from datetime import date, time
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.schemas.disponibilidad import DisponibilidadActualizar
from app.core.dependencies import obtener_usuario_actual
from app.main import app
from app.models.usuario import Usuario
from app.routers import profesionales
from app.services import disponibilidad_service


class DBFalsa:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1

    def refresh(self, objeto):
        return None


def datos(dia=3, inicio=time(14), fin=time(19)):
    return DisponibilidadActualizar(
        dia_semana=dia,
        hora_inicio=inicio,
        hora_fin=fin,
    )


def test_profesional_actualiza_franja_propia_y_excluye_la_misma(monkeypatch):
    propia = SimpleNamespace(id=8, profesional_id=4, dia_semana=3, hora_inicio=time(14), hora_fin=time(19), activa=True)
    db = DBFalsa()
    monkeypatch.setattr(disponibilidad_service, "buscar_disponibilidad_de_profesional", lambda *args: propia)
    monkeypatch.setattr(disponibilidad_service, "buscar_por_dia", lambda *args: [propia])

    resultado = disponibilidad_service.actualizar_disponibilidad_profesional(db, 8, 4, datos(inicio=time(13), fin=time(18)))

    assert resultado is propia
    assert (propia.hora_inicio, propia.hora_fin) == (time(13), time(18))
    assert db.commits == 1


@pytest.mark.parametrize("encontrada", [None])
def test_actualizar_franja_ajena_o_inexistente_devuelve_404(monkeypatch, encontrada):
    monkeypatch.setattr(disponibilidad_service, "buscar_disponibilidad_de_profesional", lambda *args: encontrada)
    with pytest.raises(HTTPException) as error:
        disponibilidad_service.actualizar_disponibilidad_profesional(DBFalsa(), 99, 4, datos())
    assert error.value.status_code == 404


def test_actualizar_rechaza_solapamiento(monkeypatch):
    propia = SimpleNamespace(id=8, activa=True)
    otra = SimpleNamespace(id=9, hora_inicio=time(14), hora_fin=time(19), activa=True)
    monkeypatch.setattr(disponibilidad_service, "buscar_disponibilidad_de_profesional", lambda *args: propia)
    monkeypatch.setattr(disponibilidad_service, "buscar_por_dia", lambda *args: [propia, otra])
    with pytest.raises(HTTPException) as error:
        disponibilidad_service.actualizar_disponibilidad_profesional(DBFalsa(), 8, 4, datos(inicio=time(18), fin=time(20)))
    assert error.value.status_code == 409


def test_actualizar_permite_adyacencia(monkeypatch):
    propia = SimpleNamespace(id=8, activa=True)
    otra = SimpleNamespace(id=9, hora_inicio=time(14), hora_fin=time(19), activa=True)
    monkeypatch.setattr(disponibilidad_service, "buscar_disponibilidad_de_profesional", lambda *args: propia)
    monkeypatch.setattr(disponibilidad_service, "buscar_por_dia", lambda *args: [otra])
    disponibilidad_service.actualizar_disponibilidad_profesional(DBFalsa(), 8, 4, datos(inicio=time(19), fin=time(21)))
    assert propia.hora_inicio == time(19)


def test_desactivar_franja_propia_no_toca_turnos(monkeypatch):
    propia = SimpleNamespace(id=8, profesional_id=4, activa=True)
    turno_existente = SimpleNamespace(id=30, estado="confirmado")
    db = DBFalsa()
    monkeypatch.setattr(disponibilidad_service, "buscar_disponibilidad_de_profesional", lambda *args: propia)

    disponibilidad_service.desactivar_disponibilidad_profesional(db, 8, 4)

    assert propia.activa is False
    assert turno_existente.estado == "confirmado"
    assert db.commits == 1


def test_franja_desactivada_deja_de_generar_slots(monkeypatch):
    propia = SimpleNamespace(
        id=8, profesional_id=4, dia_semana=0,
        hora_inicio=time(14), hora_fin=time(16), activa=True,
    )
    monkeypatch.setattr(disponibilidad_service, "buscar_disponibilidad_de_profesional", lambda *args: propia)
    disponibilidad_service.desactivar_disponibilidad_profesional(DBFalsa(), 8, 4)
    monkeypatch.setattr(
        disponibilidad_service, "buscar_prestacion",
        lambda *args: SimpleNamespace(
            activa=True, profesional_id=4, duracion_minutos=30,
            profesional=SimpleNamespace(activo=True),
        ),
    )
    monkeypatch.setattr(disponibilidad_service, "fecha_actual_negocio", lambda: date(2026, 8, 10))
    monkeypatch.setattr(
        disponibilidad_service, "buscar_por_dia",
        lambda *args: [franja for franja in [propia] if franja.activa],
    )
    monkeypatch.setattr(disponibilidad_service, "buscar_turnos_del_dia", lambda *args: [])
    monkeypatch.setattr(disponibilidad_service, "resolver_franjas_fecha", lambda db, profesional_id, fecha, habituales: habituales)

    assert disponibilidad_service.obtener_horarios_libres(DBFalsa(), 1, date(2026, 8, 17)) == []


def test_desactivar_ajena_o_inexistente_devuelve_404(monkeypatch):
    monkeypatch.setattr(disponibilidad_service, "buscar_disponibilidad_de_profesional", lambda *args: None)
    with pytest.raises(HTTPException) as error:
        disponibilidad_service.desactivar_disponibilidad_profesional(DBFalsa(), 99, 4)
    assert error.value.status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"dia_semana": 3, "hora_inicio": "19:00", "hora_fin": "14:00"},
        {"dia_semana": 3, "hora_inicio": "14:00", "hora_fin": "19:00", "profesional_id": 4},
    ],
)
def test_schema_rechaza_hora_invalida_y_profesional_id(payload):
    with pytest.raises(ValueError):
        DisponibilidadActualizar.model_validate(payload)


@pytest.fixture
def profesional_autenticado():
    app.dependency_overrides[obtener_usuario_actual] = lambda: Usuario(
        id=21, nombre="SofÃ­a", email="sofia@example.com", password_hash="hash",
        rol="profesional", activo=True,
    )
    yield
    app.dependency_overrides.pop(obtener_usuario_actual, None)


def respuesta_disponibilidad(activa=True):
    return SimpleNamespace(
        id=8, profesional_id=4, dia_semana=3,
        hora_inicio=time(14), hora_fin=time(19), activa=activa,
    )


def test_endpoints_profesionales_derivan_ownership_de_la_sesion(client, profesional_autenticado, monkeypatch):
    ids = []
    monkeypatch.setattr(profesionales, "obtener_mi_profesional", lambda *args: SimpleNamespace(id=4))
    monkeypatch.setattr(
        profesionales, "actualizar_disponibilidad_profesional",
        lambda db, disponibilidad_id, profesional_id, datos: ids.append((disponibilidad_id, profesional_id)) or respuesta_disponibilidad(),
    )
    monkeypatch.setattr(
        profesionales, "desactivar_disponibilidad_profesional",
        lambda db, disponibilidad_id, profesional_id: ids.append((disponibilidad_id, profesional_id)) or respuesta_disponibilidad(False),
    )

    editada = client.patch(
        "/profesionales/me/disponibilidades/8",
        json={"dia_semana": 3, "hora_inicio": "14:00", "hora_fin": "19:00"},
    )
    eliminada = client.delete("/profesionales/me/disponibilidades/8")

    assert editada.status_code == 200
    assert eliminada.status_code == 200
    assert ids == [(8, 4), (8, 4)]


def test_endpoint_edicion_no_acepta_profesional_id(client, profesional_autenticado, monkeypatch):
    monkeypatch.setattr(profesionales, "obtener_mi_profesional", lambda *args: SimpleNamespace(id=4))
    respuesta = client.patch(
        "/profesionales/me/disponibilidades/8",
        json={"dia_semana": 3, "hora_inicio": "14:00", "hora_fin": "19:00", "profesional_id": 9},
    )
    assert respuesta.status_code == 422
