from datetime import timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.datetime_utils import ahora_utc
from app.schemas.turno import TurnoCrear
from app.services import turno_service


def datos_turno(**cambios):
    datos = {
        "paciente_id": 1,
        "prestacion_id": 2,
        "fecha_hora": ahora_utc() + timedelta(days=2),
    }
    datos.update(cambios)
    return TurnoCrear(**datos)


def preparar(monkeypatch, *, profesional_id=10, profesional_activo=True,
             prestacion_activa=True, paciente_activo=True):
    paciente = SimpleNamespace(id=1, activo=paciente_activo)
    profesional = SimpleNamespace(id=profesional_id, activo=profesional_activo)
    prestacion = SimpleNamespace(
        id=2,
        activa=prestacion_activa,
        profesional_id=profesional_id,
        profesional=profesional,
        duracion_minutos=30,
    )
    monkeypatch.setattr(turno_service, "buscar_paciente_por_id", lambda db, paciente_id: paciente)
    monkeypatch.setattr(turno_service, "paciente_pertenece_a_profesional", lambda db, profesional_id, paciente_id: True)
    monkeypatch.setattr(turno_service, "buscar_prestacion_por_id", lambda db, prestacion_id: prestacion)
    return paciente, prestacion


def test_profesional_crea_turno_en_su_propia_agenda(monkeypatch):
    preparar(monkeypatch)
    guardado = SimpleNamespace()
    monkeypatch.setattr(turno_service, "bloquear_agenda_profesional", lambda db, profesional_id: None)
    monkeypatch.setattr(turno_service, "validar_turno_dentro_disponibilidad", lambda *args: None)
    monkeypatch.setattr(turno_service, "buscar_conflicto_horario", lambda *args, **kwargs: None)
    monkeypatch.setattr(turno_service, "guardar_turno", lambda db, datos, profesional_id, fecha_fin: guardado)
    monkeypatch.setattr(turno_service, "_confirmar_cambio_turno", lambda db, turno: turno)

    assert turno_service.crear_turno_profesional(
        SimpleNamespace(), 10, datos_turno()
    ) is guardado


def test_profesional_no_puede_usar_prestacion_ajena(monkeypatch):
    preparar(monkeypatch, profesional_id=11)
    with pytest.raises(HTTPException) as error:
        turno_service.crear_turno_profesional(SimpleNamespace(), 10, datos_turno())
    assert error.value.status_code == 404


@pytest.mark.parametrize(
    ("opciones", "detalle"),
    [
        ({"profesional_activo": False}, "profesional está inactivo"),
        ({"prestacion_activa": False}, "prestación está inactiva"),
        ({"paciente_activo": False}, "paciente está inactivo"),
    ],
)
def test_rechaza_entidades_inactivas(monkeypatch, opciones, detalle):
    preparar(monkeypatch, **opciones)
    with pytest.raises(HTTPException) as error:
        turno_service.crear_turno_profesional(SimpleNamespace(), 10, datos_turno())
    assert error.value.status_code == 400
    assert detalle.lower() in error.value.detail.lower()


def test_rechaza_fecha_pasada_para_profesional(monkeypatch):
    preparar(monkeypatch)
    with pytest.raises(HTTPException) as error:
        turno_service.crear_turno_profesional(
            SimpleNamespace(),
            10,
            datos_turno(fecha_hora=ahora_utc() - timedelta(minutes=1)),
        )
    assert error.value.status_code == 400
