from datetime import date, time
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.dependencies import obtener_usuario_actual
from app.main import app
from app.models.usuario import Usuario
from app.routers import profesionales
from app.schemas.disponibilidad_excepcion import FeriadoCrear
from app.services import disponibilidad_excepcion_service as servicio


class DBFalsa:
    def __init__(self): self.commits = 0
    def commit(self): self.commits += 1
    def refresh(self, objeto): pass
    def rollback(self): pass


def marca(origen="feriado", id=4):
    return SimpleNamespace(id=id, profesional_id=7, fecha=date(2026, 8, 20), tipo="cierre_dia", origen=origen, nombre=None, hora_inicio=None, hora_fin=None, activa=True)


@pytest.mark.parametrize("tipo,nombre", [("feriado", "San Martín"), ("no_laborable", None)])
def test_crea_feriado_o_dia_no_laborable_propio(monkeypatch, tipo, nombre):
    creado = marca(tipo)
    monkeypatch.setattr(servicio, "fecha_actual_negocio", lambda: date(2026, 8, 13))
    monkeypatch.setattr(servicio, "buscar_excepciones_activas_fecha", lambda *args: [])
    monkeypatch.setattr(servicio, "guardar_cierre_fecha", lambda db, profesional_id, fecha, origen, etiqueta: creado)
    resultado = servicio.crear_feriado(DBFalsa(), 7, FeriadoCrear(fecha=date(2026, 8, 20), tipo=tipo, nombre=nombre))
    assert resultado is creado


def test_rechaza_duplicado_aunque_cambie_tipo(monkeypatch):
    monkeypatch.setattr(servicio, "fecha_actual_negocio", lambda: date(2026, 8, 13))
    monkeypatch.setattr(servicio, "buscar_excepciones_activas_fecha", lambda *args: [marca("no_laborable")])
    with pytest.raises(HTTPException) as error:
        servicio.crear_feriado(DBFalsa(), 7, FeriadoCrear(fecha=date(2026, 8, 20), tipo="feriado"))
    assert error.value.status_code == 409


def test_schema_rechaza_profesional_id_y_nombre_excesivo():
    with pytest.raises(ValidationError):
        FeriadoCrear.model_validate({"fecha": "2026-08-20", "tipo": "feriado", "profesional_id": 8})
    with pytest.raises(ValidationError):
        FeriadoCrear(fecha=date(2026, 8, 20), tipo="feriado", nombre="x" * 121)


def test_quitar_feriado_solo_desactiva_su_marca(monkeypatch):
    feriado = marca(); vacaciones = marca("vacaciones", 5); turno = SimpleNamespace(estado="confirmado")
    monkeypatch.setattr(servicio, "buscar_feriado_propio", lambda *args: feriado)
    servicio.eliminar_feriado(DBFalsa(), 7, feriado.id)
    assert feriado.activa is False
    assert vacaciones.activa is True and turno.estado == "confirmado"


def test_quitar_feriado_ajeno_devuelve_404(monkeypatch):
    monkeypatch.setattr(servicio, "buscar_feriado_propio", lambda *args: None)
    with pytest.raises(HTTPException) as error:
        servicio.eliminar_feriado(DBFalsa(), 7, 99)
    assert error.value.status_code == 404


def test_feriado_cierra_habitual_y_extraordinaria_reabre_solo_su_franja(monkeypatch):
    extra = SimpleNamespace(id=8, tipo="franja_extraordinaria", origen="manual", hora_inicio=time(17), hora_fin=time(19))
    monkeypatch.setattr(servicio, "buscar_excepciones_activas_fecha", lambda *args: [marca(), extra])
    habitual = SimpleNamespace(hora_inicio=time(8), hora_fin=time(12))
    resultado = servicio.resolver_franjas_fecha(DBFalsa(), 7, date(2026, 8, 20), [habitual])
    assert [(item.hora_inicio, item.hora_fin) for item in resultado] == [(time(17), time(19))]


def test_fecha_se_compara_como_date_local_de_negocio(monkeypatch):
    monkeypatch.setattr(servicio, "fecha_actual_negocio", lambda: date(2026, 8, 20))
    monkeypatch.setattr(servicio, "buscar_excepciones_activas_fecha", lambda *args: [])
    with pytest.raises(HTTPException) as error:
        servicio.crear_feriado(DBFalsa(), 7, FeriadoCrear(fecha=date(2026, 8, 19), tipo="feriado"))
    assert error.value.status_code == 400


def test_endpoints_derivan_profesional_y_ocultan_ajenos(client, monkeypatch):
    app.dependency_overrides[obtener_usuario_actual] = lambda: Usuario(id=21, nombre="Sofía", email="sofia@example.com", password_hash="hash", rol="profesional", activo=True)
    monkeypatch.setattr(profesionales, "obtener_mi_profesional", lambda *args: SimpleNamespace(id=7))
    recibidos = []
    monkeypatch.setattr(profesionales, "crear_feriado", lambda db, profesional_id, datos: recibidos.append(profesional_id) or marca())
    monkeypatch.setattr(profesionales, "eliminar_feriado", lambda db, profesional_id, id: (_ for _ in ()).throw(HTTPException(404, "Feriado o día no laborable no encontrado.")))
    try:
        respuesta = client.post("/profesionales/me/feriados", json={"fecha": "2026-08-20", "tipo": "feriado"})
        assert respuesta.status_code == 201 and recibidos == [7]
        assert client.delete("/profesionales/me/feriados/99").status_code == 404
    finally:
        app.dependency_overrides.pop(obtener_usuario_actual, None)
