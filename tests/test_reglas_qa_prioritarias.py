from datetime import date, time
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.dependencies import obtener_usuario_actual
from app.main import app
from app.models.usuario import Usuario
from app.schemas.disponibilidad import DisponibilidadCrear
from app.services import disponibilidad_service, turno_service


@pytest.mark.parametrize("origen", ["finalizado", "ausente"])
@pytest.mark.parametrize(
    "destino",
    ["reservado", "confirmado", "cancelado", "ausente", "finalizado"],
)
def test_estados_terminales_no_permiten_transiciones(origen, destino):
    with pytest.raises(HTTPException) as error:
        turno_service.validar_transicion_estado(origen, destino)

    assert error.value.status_code == 409
    assert origen in error.value.detail
    assert destino in error.value.detail


@pytest.mark.parametrize(
    "inicio,fin",
    [
        (time(8), time(12)),
        (time(10), time(14)),
        (time(7), time(9)),
    ],
)
def test_rechaza_disponibilidades_duplicadas_o_solapadas(
    monkeypatch,
    inicio,
    fin,
):
    monkeypatch.setattr(
        disponibilidad_service,
        "buscar_profesional",
        lambda db, profesional_id: SimpleNamespace(activo=True),
    )
    monkeypatch.setattr(
        disponibilidad_service,
        "buscar_por_dia",
        lambda db, profesional_id, dia: [
            SimpleNamespace(hora_inicio=time(8), hora_fin=time(12))
        ],
    )

    with pytest.raises(HTTPException) as error:
        disponibilidad_service.crear_disponibilidad(
            SimpleNamespace(),
            DisponibilidadCrear(
                profesional_id=1,
                dia_semana=0,
                hora_inicio=inicio,
                hora_fin=fin,
            ),
        )

    assert error.value.status_code == 409
    assert "solapa" in error.value.detail


@pytest.mark.parametrize(
    "inicio,fin",
    [(time(6), time(8)), (time(12), time(14)), (time(14), time(18))],
)
def test_permite_disponibilidades_adyacentes_o_separadas(
    monkeypatch,
    inicio,
    fin,
):
    disponibilidad = SimpleNamespace()
    db = SimpleNamespace(
        commit=lambda: None,
        refresh=lambda objeto: None,
    )
    monkeypatch.setattr(disponibilidad_service, "buscar_profesional", lambda db, profesional_id: SimpleNamespace(activo=True))
    monkeypatch.setattr(disponibilidad_service, "buscar_por_dia", lambda db, profesional_id, dia: [SimpleNamespace(hora_inicio=time(8), hora_fin=time(12))])
    monkeypatch.setattr(disponibilidad_service, "guardar_disponibilidad", lambda db, datos: disponibilidad)

    assert disponibilidad_service.crear_disponibilidad(
        db,
        DisponibilidadCrear(profesional_id=1, dia_semana=0, hora_inicio=inicio, hora_fin=fin),
    ) is disponibilidad


def test_horarios_libres_se_deduplican_ante_datos_historicos(monkeypatch):
    prestacion = SimpleNamespace(
        activa=True,
        profesional_id=1,
        duracion_minutos=60,
    )
    horario = SimpleNamespace(hora_inicio=time(8), hora_fin=time(10))
    monkeypatch.setattr(disponibilidad_service, "buscar_prestacion", lambda db, prestacion_id: prestacion)
    monkeypatch.setattr(disponibilidad_service, "fecha_actual_negocio", lambda: date(2026, 1, 1))
    monkeypatch.setattr(disponibilidad_service, "buscar_por_dia", lambda db, profesional_id, dia: [horario, horario])
    monkeypatch.setattr(disponibilidad_service, "buscar_turnos_del_dia", lambda *args: [])

    resultado = disponibilidad_service.obtener_horarios_libres(
        SimpleNamespace(), 1, date(2026, 1, 5)
    )

    assert len(resultado) == 2
    assert len({item["fecha_hora"] for item in resultado}) == 2


@pytest.fixture
def autenticar_admin():
    app.dependency_overrides[obtener_usuario_actual] = lambda: Usuario(
        id=1,
        nombre="Admin",
        email="admin@example.com",
        password_hash="hash",
        rol="administrador",
        activo=True,
    )
    yield
    app.dependency_overrides.pop(obtener_usuario_actual, None)


def test_email_invalido_al_crear_profesional_devuelve_422(client, autenticar_admin):
    respuesta = client.post(
        "/profesionales/",
        json={
            "nombre": "Ana",
            "apellido": "Pérez",
            "matricula": "MP-001",
            "email": "no-es-email",
            "especialidades": [{"especialidad_id": 1, "duracion_turno_minutos": 30}],
        },
    )
    assert respuesta.status_code == 422


def test_email_invalido_al_editar_profesional_devuelve_422(client, autenticar_admin):
    respuesta = client.patch(
        "/profesionales/1",
        json={"email": "no-es-email"},
    )
    assert respuesta.status_code == 422
