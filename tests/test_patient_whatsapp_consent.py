from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.services import paciente_service
from app.models.paciente import Paciente
from tests.conftest import SessionTest


class DbFake:
    def commit(self): pass
    def refresh(self, item): pass


def paciente(**overrides):
    valores = dict(id=1, telefono="+54 9 351 123-4567", whatsapp_opt_in=False, whatsapp_opt_in_at=None, whatsapp_opt_out_at=None)
    valores.update(overrides)
    return SimpleNamespace(**valores)


def test_paciente_nuevo_no_tiene_opt_in_por_defecto():
    db = SessionTest()
    item = Paciente(nombre="Paciente", apellido="Prueba")
    db.add(item)
    db.commit()
    db.refresh(item)
    assert item.whatsapp_opt_in is False
    assert item.whatsapp_opt_in_at is None
    assert item.whatsapp_opt_out_at is None
    db.close()


def test_consentimiento_idempotente_y_revocable(monkeypatch):
    actual = paciente()
    monkeypatch.setattr(paciente_service, "buscar_propio", lambda *args: actual)
    primero = paciente_service.actualizar_paciente_profesional(DbFake(), 1, 1, SimpleNamespace(model_dump=lambda **kwargs: {"whatsapp_opt_in": True}))
    marcado = actual.whatsapp_opt_in_at
    assert primero.whatsapp_opt_in is True and marcado is not None and actual.whatsapp_opt_out_at is None
    paciente_service.actualizar_paciente_profesional(DbFake(), 1, 1, SimpleNamespace(model_dump=lambda **kwargs: {"whatsapp_opt_in": True}))
    assert actual.whatsapp_opt_in_at == marcado
    paciente_service.actualizar_paciente_profesional(DbFake(), 1, 1, SimpleNamespace(model_dump=lambda **kwargs: {"whatsapp_opt_in": False}))
    assert actual.whatsapp_opt_in is False and actual.whatsapp_opt_in_at == marcado and actual.whatsapp_opt_out_at is not None


def test_cambiar_telefono_revoca_consentimiento(monkeypatch):
    actual = paciente(whatsapp_opt_in=True, whatsapp_opt_in_at=datetime.now(UTC) - timedelta(days=1))
    monkeypatch.setattr(paciente_service, "buscar_propio", lambda *args: actual)
    paciente_service.actualizar_paciente_profesional(DbFake(), 1, 1, SimpleNamespace(model_dump=lambda **kwargs: {"telefono": "+54 9 11 5555-0100"}))
    assert actual.whatsapp_opt_in is False and actual.whatsapp_opt_out_at is not None


def test_cambiar_formato_sin_cambiar_numero_conserva_consentimiento(monkeypatch):
    actual = paciente(whatsapp_opt_in=True, whatsapp_opt_in_at=datetime.now(UTC) - timedelta(days=1))
    monkeypatch.setattr(paciente_service, "buscar_propio", lambda *args: actual)
    paciente_service.actualizar_paciente_profesional(
        DbFake(),
        1,
        1,
        SimpleNamespace(model_dump=lambda **kwargs: {"telefono": "0351 15 1234567"}),
    )
    assert actual.whatsapp_opt_in is True and actual.whatsapp_opt_out_at is None
