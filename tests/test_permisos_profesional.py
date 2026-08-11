from types import SimpleNamespace

import pytest

from app.core.dependencies import obtener_usuario_actual
from app.main import app
from app.models.usuario import Usuario
from app.routers import pacientes, profesionales, turnos


@pytest.fixture
def usuarios():
    return {
        rol: Usuario(
            id=indice,
            nombre=rol.title(),
            email=f"{rol}@example.com",
            password_hash="hash",
            rol=rol,
            activo=True,
        )
        for indice, rol in enumerate(
            [
                "administrador",
                "recepcionista",
                "profesional",
            ],
            start=1,
        )
    }


@pytest.fixture(autouse=True)
def limpiar_usuario_autenticado():
    yield
    app.dependency_overrides.pop(
        obtener_usuario_actual,
        None,
    )


def autenticar_como(usuario):
    app.dependency_overrides[
        obtener_usuario_actual
    ] = lambda: usuario


@pytest.mark.parametrize(
    "ruta",
    [
        "/turnos/",
        "/turnos/1",
        "/pacientes/",
        "/pacientes/1",
    ],
)
def test_profesional_no_accede_a_recursos_globales(
    client,
    usuarios,
    ruta,
):
    autenticar_como(usuarios["profesional"])

    respuesta = client.get(ruta)

    assert respuesta.status_code == 403


@pytest.mark.parametrize(
    "rol",
    [
        "administrador",
        "recepcionista",
    ],
)
def test_personal_autorizado_lista_agenda_global(
    client,
    usuarios,
    monkeypatch,
    rol,
):
    autenticar_como(usuarios[rol])
    monkeypatch.setattr(
        turnos,
        "obtener_turnos",
        lambda db: [],
    )

    respuesta = client.get("/turnos/")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


@pytest.mark.parametrize(
    "rol",
    [
        "administrador",
        "recepcionista",
    ],
)
def test_personal_autorizado_lista_pacientes(
    client,
    usuarios,
    monkeypatch,
    rol,
):
    autenticar_como(usuarios[rol])
    monkeypatch.setattr(
        pacientes,
        "obtener_pacientes",
        lambda db: [],
    )

    respuesta = client.get("/pacientes/")

    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_profesional_accede_a_su_agenda(
    client,
    usuarios,
    monkeypatch,
):
    autenticar_como(usuarios["profesional"])
    monkeypatch.setattr(
        profesionales,
        "obtener_mi_profesional",
        lambda db, usuario_id: SimpleNamespace(id=10),
    )
    monkeypatch.setattr(
        profesionales,
        "obtener_agenda_de_profesional",
        lambda db, profesional_id, estado: [],
    )

    respuesta = client.get("/profesionales/me/agenda")

    assert respuesta.status_code == 200
    assert respuesta.json() == []
