import pytest

from app.core.dependencies import obtener_usuario_actual
from app.main import app
from app.models.usuario import Usuario


ROLES_NO_ADMINISTRATIVOS = (
    "recepcionista",
    "profesional",
    "paciente",
)


def usuario(rol: str) -> Usuario:
    return Usuario(
        id=1,
        nombre=rol.title(),
        email=f"{rol}@example.com",
        password_hash="hash",
        rol=rol,
        activo=True,
    )


def autenticar_como(rol: str) -> None:
    app.dependency_overrides[
        obtener_usuario_actual
    ] = lambda: usuario(rol)


@pytest.fixture(autouse=True)
def limpiar_usuario_autenticado():
    yield
    app.dependency_overrides.pop(
        obtener_usuario_actual,
        None,
    )


def crear_especialidad(client) -> int:
    respuesta = client.post(
        "/especialidades/",
        json={
            "nombre": "Clínica Médica",
            "duracion_turno_minutos": 30,
        },
    )

    assert respuesta.status_code == 201
    return respuesta.json()["id"]


def crear_profesional(
    client,
    especialidad_id: int,
    matricula: str,
    email: str | None = None,
) -> dict:
    respuesta = client.post(
        "/profesionales/",
        json={
            "nombre": "Ana",
            "apellido": "Pérez",
            "matricula": matricula,
            "telefono": "+54 11 5555-1234",
            "email": email,
            "especialidades": [
                {
                    "especialidad_id": especialidad_id,
                    "duracion_turno_minutos": 45,
                }
            ],
        },
    )

    assert respuesta.status_code == 201
    return respuesta.json()


def test_actualiza_parcialmente_datos_basicos(client):
    autenticar_como("administrador")
    especialidad_id = crear_especialidad(client)
    profesional = crear_profesional(
        client,
        especialidad_id,
        "MP-EDIT-001",
        "ana@example.com",
    )

    respuesta = client.patch(
        f"/profesionales/{profesional['id']}",
        json={
            "nombre": "Anabella",
            "email": None,
        },
    )

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["nombre"] == "Anabella"
    assert datos["email"] is None
    assert datos["apellido"] == "Pérez"
    assert datos["matricula"] == "MP-EDIT-001"
    assert datos["telefono"] == "+54 11 5555-1234"


@pytest.mark.parametrize(
    "rol",
    ROLES_NO_ADMINISTRATIVOS,
)
def test_rechaza_actualizacion_para_no_administradores(
    client,
    rol,
):
    autenticar_como(rol)

    respuesta = client.patch(
        "/profesionales/1",
        json={"nombre": "Nombre nuevo"},
    )

    assert respuesta.status_code == 403


def test_devuelve_404_si_el_profesional_no_existe(client):
    autenticar_como("administrador")

    respuesta = client.patch(
        "/profesionales/999",
        json={"nombre": "Nombre nuevo"},
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == (
        "Profesional no encontrado."
    )


def test_rechaza_conflicto_de_matricula(client):
    autenticar_como("administrador")
    especialidad_id = crear_especialidad(client)
    primero = crear_profesional(
        client,
        especialidad_id,
        "MP-EDIT-001",
    )
    segundo = crear_profesional(
        client,
        especialidad_id,
        "MP-EDIT-002",
    )

    respuesta = client.patch(
        f"/profesionales/{segundo['id']}",
        json={"matricula": primero["matricula"]},
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == (
        "Ya existe un profesional con esa matrícula."
    )

    consulta = client.get(
        f"/profesionales/{segundo['id']}"
    )
    assert consulta.status_code == 200
    assert consulta.json()["matricula"] == "MP-EDIT-002"
