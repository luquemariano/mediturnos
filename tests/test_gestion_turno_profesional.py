from datetime import timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.datetime_utils import ahora_utc
from app.schemas.turno import TurnoReprogramar
from app.services import turno_service


class DbFalsa:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass

    def refresh(self, objeto):
        pass


def turno(estado="confirmado", profesional_id=10):
    prestacion = SimpleNamespace(id=3, duracion_minutos=50)
    return SimpleNamespace(
        id=1,
        estado=estado,
        profesional_id=profesional_id,
        paciente_id=2,
        prestacion_id=3,
        prestacion=prestacion,
        fecha_hora=ahora_utc() + timedelta(days=1),
        fecha_fin=ahora_utc() + timedelta(days=1, minutes=50),
        pago=SimpleNamespace(estado="approved", requiere_revision=False),
    )


def test_profesional_cancela_turno_propio_y_conserva_pago(monkeypatch):
    actual = turno()
    pago = actual.pago
    monkeypatch.setattr(turno_service, "buscar_turno_de_profesional", lambda db, turno_id, profesional_id: actual)

    resultado = turno_service.cancelar_turno_profesional(DbFalsa(), 1, 10)

    assert resultado.estado == "cancelado"
    assert resultado.pago is pago
    assert resultado.pago.estado == "approved"


def test_cancelacion_profesional_es_idempotente(monkeypatch):
    actual = turno("cancelado")
    monkeypatch.setattr(turno_service, "buscar_turno_de_profesional", lambda *args: actual)
    assert turno_service.cancelar_turno_profesional(DbFalsa(), 1, 10).estado == "cancelado"


@pytest.mark.parametrize("estado", ["finalizado", "ausente"])
def test_profesional_no_cancela_estado_terminal(monkeypatch, estado):
    monkeypatch.setattr(turno_service, "buscar_turno_de_profesional", lambda *args: turno(estado))
    with pytest.raises(HTTPException) as error:
        turno_service.cancelar_turno_profesional(DbFalsa(), 1, 10)
    assert error.value.status_code == 409


def test_profesional_no_cancela_turno_ajeno_o_inexistente(monkeypatch):
    monkeypatch.setattr(turno_service, "buscar_turno_de_profesional", lambda *args: None)
    with pytest.raises(HTTPException) as error:
        turno_service.cancelar_turno_profesional(DbFalsa(), 99, 10)
    assert error.value.status_code == 404


def preparar_reprogramacion(monkeypatch, actual):
    monkeypatch.setattr(turno_service, "buscar_turno_de_profesional", lambda *args: actual)
    monkeypatch.setattr(turno_service, "bloquear_agenda_profesional", lambda *args: None)
    monkeypatch.setattr(turno_service, "validar_turno_dentro_disponibilidad", lambda *args: None)
    monkeypatch.setattr(turno_service, "buscar_conflicto_horario", lambda *args, **kwargs: None)


def test_profesional_reprograma_turno_propio_conservando_relaciones_y_pago(monkeypatch):
    actual = turno()
    paciente_id, prestacion_id, pago = actual.paciente_id, actual.prestacion_id, actual.pago
    preparar_reprogramacion(monkeypatch, actual)
    nueva_fecha = ahora_utc() + timedelta(days=4)

    resultado = turno_service.reprogramar_turno_profesional(
        DbFalsa(), 1, 10, TurnoReprogramar(fecha_hora=nueva_fecha),
    )

    assert resultado.fecha_hora == nueva_fecha
    assert resultado.fecha_fin == nueva_fecha + timedelta(minutes=50)
    assert resultado.paciente_id == paciente_id
    assert resultado.prestacion_id == prestacion_id
    assert resultado.pago is pago
    assert resultado.pago.estado == "approved"


def test_profesional_no_reprograma_turno_ajeno(monkeypatch):
    monkeypatch.setattr(turno_service, "buscar_turno_de_profesional", lambda *args: None)
    with pytest.raises(HTTPException) as error:
        turno_service.reprogramar_turno_profesional(
            DbFalsa(), 1, 10, TurnoReprogramar(fecha_hora=ahora_utc() + timedelta(days=2)),
        )
    assert error.value.status_code == 404


def test_profesional_no_reprograma_fecha_pasada(monkeypatch):
    actual = turno()
    monkeypatch.setattr(turno_service, "buscar_turno_de_profesional", lambda *args: actual)
    with pytest.raises(HTTPException) as error:
        turno_service.reprogramar_turno_profesional(
            DbFalsa(), 1, 10, TurnoReprogramar(fecha_hora=ahora_utc() - timedelta(minutes=1)),
        )
    assert error.value.status_code == 400


@pytest.mark.parametrize("estado", ["cancelado", "finalizado", "ausente"])
def test_profesional_no_reprograma_turno_terminal(monkeypatch, estado):
    monkeypatch.setattr(turno_service, "buscar_turno_de_profesional", lambda *args: turno(estado))
    with pytest.raises(HTTPException) as error:
        turno_service.reprogramar_turno_profesional(
            DbFalsa(), 1, 10, TurnoReprogramar(fecha_hora=ahora_utc() + timedelta(days=2)),
        )
    assert error.value.status_code == 400


def test_reprogramacion_reutiliza_validacion_de_disponibilidad(monkeypatch):
    actual = turno()
    monkeypatch.setattr(turno_service, "buscar_turno_de_profesional", lambda *args: actual)
    monkeypatch.setattr(turno_service, "bloquear_agenda_profesional", lambda *args: None)
    monkeypatch.setattr(
        turno_service,
        "validar_turno_dentro_disponibilidad",
        lambda *args: (_ for _ in ()).throw(HTTPException(status_code=400, detail="fuera de disponibilidad")),
    )
    with pytest.raises(HTTPException) as error:
        turno_service.reprogramar_turno_profesional(
            DbFalsa(), 1, 10, TurnoReprogramar(fecha_hora=ahora_utc() + timedelta(days=2)),
        )
    assert error.value.detail == "fuera de disponibilidad"


def test_reprogramacion_excluye_turno_actual_y_rechaza_conflicto(monkeypatch):
    actual = turno()
    preparar_reprogramacion(monkeypatch, actual)
    recibido = {}

    def conflicto(*args, **kwargs):
        recibido.update(kwargs)
        return SimpleNamespace(id=2)

    monkeypatch.setattr(turno_service, "buscar_conflicto_horario", conflicto)
    with pytest.raises(HTTPException) as error:
        turno_service.reprogramar_turno_profesional(
            DbFalsa(), 1, 10, TurnoReprogramar(fecha_hora=ahora_utc() + timedelta(days=2)),
        )
    assert recibido["turno_id_excluido"] == 1
    assert error.value.status_code == 409
