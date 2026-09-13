from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.core.worker_config import AppointmentReminderWorkerSettings
from app.scripts import waitlist_offer_worker as worker


class StopAfterOne:
    def __init__(self):
        self.waits = []
        self.checks = 0

    def is_set(self):
        self.checks += 1
        return self.checks > 1

    def wait(self, interval):
        self.waits.append(interval)


def config(interval=17):
    return MagicMock(waitlist_offer_worker_interval_seconds=interval)


def test_process_once_sigue_expirando_ofertas(monkeypatch):
    db = MagicMock()
    inicio = datetime.now(timezone.utc)
    expired_offer = SimpleNamespace(profesional_id=1, prestacion_id=2, slot_inicio=inicio, slot_fin=inicio + timedelta(minutes=30))
    recibidos = []
    monkeypatch.setattr(worker, "expire_waitlist_offers", lambda db, now: [expired_offer])
    monkeypatch.setattr(worker, "process_released_slot_waitlist", lambda db, released_slot: recibidos.append(released_slot) or "offered")
    assert worker.process_once(db) == 1
    assert len(recibidos) == 1
    assert recibidos[0].profesional_id == 1
    assert recibidos[0].prestacion_id == 2
    assert recibidos[0].fecha_hora == inicio
    assert recibidos[0].fecha_fin == expired_offer.slot_fin


def test_loop_abre_y_cierra_sesion_en_cada_iteracion(monkeypatch):
    db = MagicMock(); factory = MagicMock(return_value=db); stop = StopAfterOne()
    monkeypatch.setattr(worker, "process_once", lambda db: None)
    worker.run_forever(config(), session_factory=factory, stop=stop)
    factory.assert_called_once_with()
    db.commit.assert_called_once_with()
    db.close.assert_called_once_with()
    assert stop.waits == [17]


def test_error_de_iteracion_hace_rollback_cierra_y_continua(monkeypatch):
    primero, segundo = MagicMock(), MagicMock(); factory = MagicMock(side_effect=[primero, segundo]); stop = StopAfterOne(); llamadas = []
    monkeypatch.setattr(worker, "process_once", lambda db: llamadas.append(db) or (_ for _ in ()).throw(RuntimeError("fallo")))
    worker.run_forever(config(9), session_factory=factory, stop=stop)
    assert llamadas == [primero]
    primero.rollback.assert_called_once_with(); primero.close.assert_called_once_with()
    assert stop.waits == [9]


def test_intervalo_invalido_falla_configuracion():
    with pytest.raises(ValidationError):
        AppointmentReminderWorkerSettings(_env_file=None, database_url="sqlite:///worker.db", app_env="test", waitlist_offer_worker_interval_seconds=0)
