from datetime import date, datetime, time
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.disponibilidad_excepcion import DisponibilidadExcepcionCrear
from app.services import disponibilidad_excepcion_service as servicio
from app.services import disponibilidad_service


class DBFalsa:
    def __init__(self): self.commits = 0; self.rollback_hecho = False
    def commit(self): self.commits += 1
    def refresh(self, objeto): pass
    def rollback(self): self.rollback_hecho = True


def excepcion(tipo="cierre_dia", inicio=None, fin=None, id=1):
    return SimpleNamespace(id=id, profesional_id=7, fecha=date(2026, 8, 20), tipo=tipo, hora_inicio=inicio, hora_fin=fin, activa=True)


def datos(tipo="cierre_dia", inicio=None, fin=None):
    return DisponibilidadExcepcionCrear(fecha=date(2026, 8, 20), tipo=tipo, hora_inicio=inicio, hora_fin=fin)


def test_crea_cierre_propio(monkeypatch):
    creado = excepcion()
    monkeypatch.setattr(servicio, "buscar_excepciones_activas_fecha", lambda *args: [])
    monkeypatch.setattr(servicio, "fecha_actual_negocio", lambda: date(2026, 8, 13))
    monkeypatch.setattr(servicio, "guardar_excepcion", lambda db, profesional_id, datos: creado)
    assert servicio.crear_excepcion(DBFalsa(), 7, datos()) is creado


def test_rechaza_cierre_duplicado(monkeypatch):
    monkeypatch.setattr(servicio, "fecha_actual_negocio", lambda: date(2026, 8, 13))
    monkeypatch.setattr(servicio, "buscar_excepciones_activas_fecha", lambda *args: [excepcion()])
    with pytest.raises(HTTPException) as error: servicio.crear_excepcion(DBFalsa(), 7, datos())
    assert error.value.status_code == 409


@pytest.mark.parametrize("payload", [
    {"fecha": "2026-08-20", "tipo": "franja_extraordinaria", "hora_inicio": "14:00", "hora_fin": "14:00"},
    {"fecha": "2026-08-20", "tipo": "cierre_dia", "profesional_id": 9},
])
def test_rechaza_horario_invalido_y_profesional_id(payload):
    with pytest.raises(ValidationError): DisponibilidadExcepcionCrear.model_validate(payload)


def test_rechaza_solapamiento_extraordinario(monkeypatch):
    monkeypatch.setattr(servicio, "fecha_actual_negocio", lambda: date(2026, 8, 13))
    otra = excepcion("franja_extraordinaria", time(14), time(18))
    monkeypatch.setattr(servicio, "buscar_excepciones_activas_fecha", lambda *args: [otra])
    with pytest.raises(HTTPException) as error:
        servicio.crear_excepcion(DBFalsa(), 7, datos("franja_extraordinaria", time(17), time(19)))
    assert error.value.status_code == 409


def test_permite_adyacencia_extraordinaria(monkeypatch):
    monkeypatch.setattr(servicio, "fecha_actual_negocio", lambda: date(2026, 8, 13))
    creada = excepcion("franja_extraordinaria", time(18), time(20), 2)
    monkeypatch.setattr(servicio, "buscar_excepciones_activas_fecha", lambda *args: [excepcion("franja_extraordinaria", time(14), time(18))])
    monkeypatch.setattr(servicio, "guardar_excepcion", lambda *args: creada)
    assert servicio.crear_excepcion(DBFalsa(), 7, datos("franja_extraordinaria", time(18), time(20))) is creada


def test_elimina_propia_sin_tocar_turnos(monkeypatch):
    item = excepcion(); turno = SimpleNamespace(estado="confirmado"); db = DBFalsa()
    monkeypatch.setattr(servicio, "buscar_excepcion_propia", lambda *args: item)
    servicio.eliminar_excepcion(db, 7, 1)
    assert item.activa is False and turno.estado == "confirmado"


def test_eliminar_ajena_o_inexistente_devuelve_404(monkeypatch):
    monkeypatch.setattr(servicio, "buscar_excepcion_propia", lambda *args: None)
    with pytest.raises(HTTPException) as error: servicio.eliminar_excepcion(DBFalsa(), 7, 99)
    assert error.value.status_code == 404


def test_cierre_elimina_habituales(monkeypatch):
    monkeypatch.setattr(servicio, "buscar_excepciones_activas_fecha", lambda *args: [excepcion()])
    habitual = SimpleNamespace(hora_inicio=time(8), hora_fin=time(12))
    assert servicio.resolver_franjas_fecha(DBFalsa(), 7, date(2026, 8, 20), [habitual]) == []


def test_extraordinaria_genera_franja_sin_habitual(monkeypatch):
    extra = excepcion("franja_extraordinaria", time(9), time(13))
    monkeypatch.setattr(servicio, "buscar_excepciones_activas_fecha", lambda *args: [extra])
    resultado = servicio.resolver_franjas_fecha(DBFalsa(), 7, date(2026, 8, 22), [])
    assert [(x.hora_inicio, x.hora_fin) for x in resultado] == [(time(9), time(13))]


def test_cierre_mas_extraordinaria_deja_solo_extra(monkeypatch):
    extra = excepcion("franja_extraordinaria", time(17), time(19), 2)
    monkeypatch.setattr(servicio, "buscar_excepciones_activas_fecha", lambda *args: [excepcion(), extra])
    habitual = SimpleNamespace(hora_inicio=time(8), hora_fin=time(12))
    resultado = servicio.resolver_franjas_fecha(DBFalsa(), 7, date(2026, 8, 20), [habitual])
    assert [(x.hora_inicio, x.hora_fin) for x in resultado] == [(time(17), time(19))]


def test_validacion_turno_usa_excepciones_para_creacion_y_reprogramacion(monkeypatch):
    monkeypatch.setattr(disponibilidad_service, "buscar_por_dia", lambda *args: [])
    monkeypatch.setattr(disponibilidad_service, "resolver_franjas_fecha", lambda *args: [SimpleNamespace(hora_inicio=time(17), hora_fin=time(19))])
    disponibilidad_service.validar_turno_dentro_disponibilidad(DBFalsa(), 7, datetime.fromisoformat("2026-08-20T17:00:00-03:00"), 60)
    with pytest.raises(HTTPException):
        disponibilidad_service.validar_turno_dentro_disponibilidad(DBFalsa(), 7, datetime.fromisoformat("2026-08-20T10:00:00-03:00"), 60)
