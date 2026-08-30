from datetime import datetime
from datetime import datetime
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
        "/prestaciones/",
        "/prestaciones/1",
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


def test_agenda_profesional_propaga_rango_y_estado(
    client,
    usuarios,
    monkeypatch,
):
    autenticar_como(usuarios["profesional"])
    monkeypatch.setattr(profesionales, "obtener_mi_profesional", lambda db, usuario_id: SimpleNamespace(id=10))
    recibido = {}
    monkeypatch.setattr(profesionales, "obtener_agenda_de_profesional", lambda db, profesional_id, estado, desde=None, hasta=None: recibido.update(profesional_id=profesional_id, estado=estado, desde=desde, hasta=hasta) or [])

    respuesta = client.get("/profesionales/me/agenda?estado=confirmado&desde=2026-08-31&hasta=2026-09-06")

    assert respuesta.status_code == 200
    assert recibido["profesional_id"] == 10
    assert recibido["estado"] == "confirmado"
    assert str(recibido["desde"]) == "2026-08-31"
    assert str(recibido["hasta"]) == "2026-09-06"


def test_agenda_profesional_rechaza_rango_invertido(client, usuarios, monkeypatch):
    autenticar_como(usuarios["profesional"])
    monkeypatch.setattr(profesionales, "obtener_mi_profesional", lambda db, usuario_id: SimpleNamespace(id=10))
    respuesta = client.get("/profesionales/me/agenda?desde=2026-09-06&hasta=2026-08-31")
    assert respuesta.status_code == 422


def test_agenda_profesional_incluye_fecha_fin(client, usuarios, monkeypatch):
    autenticar_como(usuarios["profesional"])
    monkeypatch.setattr(profesionales, "obtener_mi_profesional", lambda db, usuario_id: SimpleNamespace(id=10))
    monkeypatch.setattr(profesionales, "obtener_agenda_de_profesional", lambda *args: [{
        "id": 1, "paciente_id": 2, "paciente_nombre": "Ana López",
        "prestacion_id": 3, "prestacion_nombre": "Consulta",
        "profesional_nombre": "Sofía Ramírez", "especialidad_nombre": "Clínica",
        "fecha_hora": datetime.fromisoformat("2026-08-31T12:00:00+00:00"),
        "fecha_fin": datetime.fromisoformat("2026-08-31T12:50:00+00:00"),
        "estado": "confirmado", "observaciones": None,
    }])
    respuesta = client.get("/profesionales/me/agenda?desde=2026-08-31&hasta=2026-08-31")
    assert respuesta.status_code == 200
    assert respuesta.json()[0]["fecha_fin"] == "2026-08-31T12:50:00Z"


def test_profesional_lista_solo_datos_minimos_de_pacientes(
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
        "obtener_pacientes_profesional",
        lambda db, profesional_id, q: [SimpleNamespace(id=2, nombre="Ana", apellido="López", dni=None, telefono=None, email=None, fecha_nacimiento=None)],
    )

    respuesta = client.get("/profesionales/me/pacientes")

    assert respuesta.status_code == 200
    assert respuesta.json() == [{"id": 2, "nombre": "Ana", "apellido": "López", "dni": None, "telefono": None, "email": None, "fecha_nacimiento": None}]


def test_profesional_crea_turno_sin_elegir_profesional(
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
    recibido = {}

    def crear(db, profesional_id, datos):
        recibido.update(profesional_id=profesional_id, datos=datos)
        return {
            "id": 1, "paciente_id": 2, "paciente_nombre": "Ana López",
            "prestacion_id": 3, "prestacion_nombre": "Consulta",
            "profesional_nombre": "Sofía Ramírez", "especialidad_nombre": "Clínica",
            "fecha_hora": datetime.fromisoformat("2030-01-01T12:00:00+00:00"), "estado": "reservado",
            "observaciones": None,
        }

    monkeypatch.setattr(profesionales, "crear_turno_profesional", crear)
    respuesta = client.post("/profesionales/me/turnos", json={
        "paciente_id": 2,
        "prestacion_id": 3,
        "fecha_hora": "2030-01-01T09:00:00-03:00",
        "observaciones": None,
    })

    assert respuesta.status_code == 201
    assert recibido["profesional_id"] == 10
    assert not hasattr(recibido["datos"], "profesional_id")


def test_endpoint_profesional_rechaza_profesional_id_y_otros_roles(
    client,
    usuarios,
):
    payload = {
        "paciente_id": 2,
        "prestacion_id": 3,
        "profesional_id": 99,
        "fecha_hora": "2030-01-01T09:00:00-03:00",
    }
    autenticar_como(usuarios["profesional"])
    assert client.post("/profesionales/me/turnos", json=payload).status_code == 422

    payload.pop("profesional_id")
    autenticar_como(usuarios["administrador"])
    assert client.post("/profesionales/me/turnos", json=payload).status_code == 403
    assert client.get("/profesionales/me/pacientes").status_code == 403


def test_endpoints_gestion_agenda_profesional_resuelven_ownership(
    client,
    usuarios,
    monkeypatch,
):
    autenticar_como(usuarios["profesional"])
    monkeypatch.setattr(profesionales, "obtener_mi_profesional", lambda *args: SimpleNamespace(id=10))
    cancelado = {}
    reprogramado = {}

    def cancelar(db, turno_id, profesional_id):
        cancelado.update(turno_id=turno_id, profesional_id=profesional_id)
        return {
            "id": turno_id, "paciente_id": 2, "paciente_nombre": "Ana López",
            "prestacion_id": 3, "prestacion_nombre": "Consulta", "profesional_nombre": "Sofía Ramírez",
            "especialidad_nombre": "Clínica", "fecha_hora": datetime.fromisoformat("2030-01-01T12:00:00+00:00"),
            "estado": "cancelado", "observaciones": None,
        }

    def reprogramar(db, turno_id, profesional_id, datos):
        reprogramado.update(turno_id=turno_id, profesional_id=profesional_id, fecha=datos.fecha_hora)
        return {
            "id": turno_id, "paciente_id": 2, "paciente_nombre": "Ana López",
            "prestacion_id": 3, "prestacion_nombre": "Consulta", "profesional_nombre": "Sofía Ramírez",
            "especialidad_nombre": "Clínica", "fecha_hora": datos.fecha_hora,
            "estado": "confirmado", "observaciones": None,
        }

    monkeypatch.setattr(profesionales, "cancelar_turno_profesional", cancelar)
    monkeypatch.setattr(profesionales, "reprogramar_turno_profesional", reprogramar)
    assert client.patch("/profesionales/me/agenda/7/cancelar").status_code == 200
    assert client.patch("/profesionales/me/agenda/7/reprogramar", json={"fecha_hora": "2030-01-02T09:00:00-03:00"}).status_code == 200
    assert cancelado == {"turno_id": 7, "profesional_id": 10}
    assert reprogramado["turno_id"] == 7
    assert reprogramado["profesional_id"] == 10
