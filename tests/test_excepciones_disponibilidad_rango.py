from datetime import date
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.schemas.disponibilidad_excepcion import DisponibilidadExcepcionRango
from app.services import disponibilidad_excepcion_service as servicio
from app.core.dependencies import obtener_usuario_actual
from app.main import app
from app.models.usuario import Usuario
from app.routers import profesionales


class DBFalsa:
    def __init__(self, fallar=False): self.commits = 0; self.rollback_hecho = False; self.fallar = fallar
    def commit(self):
        self.commits += 1
        if self.fallar: raise IntegrityError("sql", {}, Exception("conflicto"))
    def rollback(self): self.rollback_hecho = True


def cierre(fecha): return SimpleNamespace(fecha=fecha, tipo="cierre_dia", activa=True)


@pytest.mark.parametrize("desde,hasta,dias", [
    (date(2026, 9, 12), date(2026, 9, 20), 9),
    (date(2026, 9, 12), date(2026, 9, 12), 1),
    (date(2026, 1, 1), date(2026, 12, 31), 365),
])
def test_crear_rango_valido_incluye_limites(monkeypatch, desde, hasta, dias):
    creados = []
    monkeypatch.setattr(servicio, "fecha_actual_negocio", lambda: date(2026, 1, 1))
    monkeypatch.setattr(servicio, "buscar_cierres_activos_rango", lambda *args: [])
    monkeypatch.setattr(servicio, "guardar_cierre_fecha", lambda db, profesional_id, fecha: creados.append(fecha))
    resultado = servicio.cerrar_rango(DBFalsa(), 7, desde, hasta)
    assert resultado == {"creados": dias, "ya_existentes": 0}
    assert len(creados) == dias


@pytest.mark.parametrize("payload", [
    {"fecha_desde": "2026-09-20", "fecha_hasta": "2026-09-12"},
    {"fecha_desde": "2026-01-01", "fecha_hasta": "2027-01-01"},
    {"fecha_desde": "2026-09-12", "fecha_hasta": "2026-09-20", "profesional_id": 8},
])
def test_schema_rechaza_rango_invalido_excesivo_y_profesional_id(payload):
    with pytest.raises(ValidationError): DisponibilidadExcepcionRango.model_validate(payload)


def test_cierres_existentes_no_se_duplican_y_extraordinaria_no_se_toca(monkeypatch):
    existentes = [cierre(date(2026, 9, 13)), cierre(date(2026, 9, 15))]
    extra = SimpleNamespace(fecha=date(2026, 9, 14), tipo="franja_extraordinaria", activa=True)
    creados = []
    monkeypatch.setattr(servicio, "fecha_actual_negocio", lambda: date(2026, 9, 1))
    monkeypatch.setattr(servicio, "buscar_cierres_activos_rango", lambda *args: existentes)
    monkeypatch.setattr(servicio, "guardar_cierre_fecha", lambda db, profesional_id, fecha: creados.append(fecha))
    resultado = servicio.cerrar_rango(DBFalsa(), 7, date(2026, 9, 12), date(2026, 9, 15))
    assert resultado == {"creados": 2, "ya_existentes": 2}
    assert extra.activa is True


def test_creacion_es_transaccional_y_hace_rollback(monkeypatch):
    monkeypatch.setattr(servicio, "fecha_actual_negocio", lambda: date(2026, 9, 1))
    monkeypatch.setattr(servicio, "buscar_cierres_activos_rango", lambda *args: [])
    monkeypatch.setattr(servicio, "guardar_cierre_fecha", lambda *args: None)
    db = DBFalsa(fallar=True)
    with pytest.raises(HTTPException) as error:
        servicio.cerrar_rango(db, 7, date(2026, 9, 12), date(2026, 9, 20))
    assert error.value.status_code == 409 and db.rollback_hecho


def test_reabrir_rango_desactiva_solo_cierres(monkeypatch):
    cierres = [cierre(date(2026, 9, 12)), cierre(date(2026, 9, 13))]
    extra = SimpleNamespace(tipo="franja_extraordinaria", activa=True)
    turno = SimpleNamespace(estado="confirmado")
    monkeypatch.setattr(servicio, "buscar_cierres_activos_rango", lambda *args: cierres)
    resultado = servicio.reabrir_rango(DBFalsa(), 7, date(2026, 9, 12), date(2026, 9, 20))
    assert resultado == {"reabiertos": 2}
    assert all(not item.activa for item in cierres)
    assert extra.activa is True and turno.estado == "confirmado"


def test_endpoints_derivan_ownership_de_sesion(client, monkeypatch):
    app.dependency_overrides[obtener_usuario_actual] = lambda: Usuario(
        id=21, nombre="Sofía", email="sofia@example.com", password_hash="hash", rol="profesional", activo=True,
    )
    monkeypatch.setattr(profesionales, "obtener_mi_profesional", lambda *args: SimpleNamespace(id=7))
    recibidos = []
    monkeypatch.setattr(profesionales, "cerrar_rango", lambda db, profesional_id, desde, hasta: recibidos.append(profesional_id) or {"creados": 9, "ya_existentes": 0})
    monkeypatch.setattr(profesionales, "reabrir_rango", lambda db, profesional_id, desde, hasta: recibidos.append(profesional_id) or {"reabiertos": 9})
    payload = {"fecha_desde": "2026-09-12", "fecha_hasta": "2026-09-20"}
    try:
        assert client.post("/profesionales/me/excepciones-disponibilidad/rango", json=payload).status_code == 200
        assert client.post("/profesionales/me/excepciones-disponibilidad/reabrir-rango", json=payload).status_code == 200
        assert recibidos == [7, 7]
    finally:
        app.dependency_overrides.pop(obtener_usuario_actual, None)
