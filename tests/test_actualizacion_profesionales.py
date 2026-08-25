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


def crear_especialidad(
    client,
    nombre: str = "Clínica Médica",
    duracion_turno_minutos: int = 30,
) -> int:
    respuesta = client.post(
        "/especialidades/",
        json={
            "nombre": nombre,
            "duracion_turno_minutos": (
                duracion_turno_minutos
            ),
        },
    )

    assert respuesta.status_code == 201
    return respuesta.json()["id"]


def crear_profesional(
    client,
    especialidad_id: int,
    matricula: str,
    email: str | None = None,
    especialidades: list[dict] | None = None,
) -> dict:
    respuesta = client.post(
        "/profesionales/",
        json={
            "nombre": "Ana",
            "apellido": "Pérez",
            "matricula": matricula,
            "telefono": "+54 11 5555-1234",
            "email": email,
            "especialidades": especialidades or [
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


def test_actualiza_especialidad_y_duracion(client):
    autenticar_como("administrador")
    especialidad_id = crear_especialidad(client)
    profesional = crear_profesional(
        client,
        especialidad_id,
        "MP-EDIT-001",
    )

    respuesta = client.patch(
        f"/profesionales/{profesional['id']}",
        json={
            "especialidades": [
                {
                    "especialidad_id": especialidad_id,
                    "duracion_turno_minutos": 60,
                }
            ]
        },
    )

    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["nombre"] == "Ana"
    assert datos["matricula"] == "MP-EDIT-001"
    assert datos["especialidades"] == [
        {
            "especialidad_id": especialidad_id,
            "duracion_turno_minutos": 60,
        }
    ]


def test_actualiza_multiples_especialidades(client):
    autenticar_como("administrador")
    clinica_id = crear_especialidad(client)
    cardiologia_id = crear_especialidad(
        client,
        "Cardiología",
        40,
    )
    profesional = crear_profesional(
        client,
        clinica_id,
        "MP-EDIT-001",
    )

    respuesta = client.patch(
        f"/profesionales/{profesional['id']}",
        json={
            "especialidades": [
                {
                    "especialidad_id": clinica_id,
                    "duracion_turno_minutos": 30,
                },
                {
                    "especialidad_id": cardiologia_id,
                    "duracion_turno_minutos": 50,
                },
            ]
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["especialidades"] == [
        {
            "especialidad_id": clinica_id,
            "duracion_turno_minutos": 30,
        },
        {
            "especialidad_id": cardiologia_id,
            "duracion_turno_minutos": 50,
        },
    ]


def test_rechaza_especialidad_inexistente(client):
    autenticar_como("administrador")
    especialidad_id = crear_especialidad(client)
    profesional = crear_profesional(
        client,
        especialidad_id,
        "MP-EDIT-001",
    )

    respuesta = client.patch(
        f"/profesionales/{profesional['id']}",
        json={
            "especialidades": [
                {
                    "especialidad_id": 999,
                    "duracion_turno_minutos": 40,
                }
            ]
        },
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == (
        "Una o más especialidades no existen."
    )

    consulta = client.get(
        f"/profesionales/{profesional['id']}"
    )
    assert consulta.json()["especialidades"] == [
        {
            "especialidad_id": especialidad_id,
            "duracion_turno_minutos": 45,
        }
    ]


def test_rechaza_especialidades_duplicadas(client):
    autenticar_como("administrador")
    especialidad_id = crear_especialidad(client)
    profesional = crear_profesional(
        client,
        especialidad_id,
        "MP-EDIT-001",
    )

    respuesta = client.patch(
        f"/profesionales/{profesional['id']}",
        json={
            "especialidades": [
                {
                    "especialidad_id": especialidad_id,
                    "duracion_turno_minutos": 30,
                },
                {
                    "especialidad_id": especialidad_id,
                    "duracion_turno_minutos": 50,
                },
            ]
        },
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == (
        "No se puede repetir una especialidad."
    )


def crear_prestacion(
    client,
    profesional_id: int,
    especialidad_id: int,
) -> dict:
    respuesta = client.post(
        "/prestaciones/",
        json={
            "nombre": "Consulta asociada",
            "descripcion": None,
            "duracion_minutos": 40,
            "precio": "25000.00",
            "modalidad": "presencial",
            "profesional_id": profesional_id,
            "especialidad_id": especialidad_id,
        },
    )

    assert respuesta.status_code == 201
    return respuesta.json()


def crear_profesional_con_dos_especialidades(client):
    clinica_id = crear_especialidad(client)
    cardiologia_id = crear_especialidad(
        client,
        "Cardiología",
        40,
    )
    profesional = crear_profesional(
        client,
        clinica_id,
        "MP-EDIT-001",
        especialidades=[
            {
                "especialidad_id": clinica_id,
                "duracion_turno_minutos": 45,
            },
            {
                "especialidad_id": cardiologia_id,
                "duracion_turno_minutos": 40,
            },
        ],
    )

    return profesional, clinica_id, cardiologia_id


def test_quita_especialidad_sin_prestaciones(client):
    autenticar_como("administrador")
    profesional, clinica_id, _ = (
        crear_profesional_con_dos_especialidades(
            client
        )
    )

    respuesta = client.patch(
        f"/profesionales/{profesional['id']}",
        json={
            "especialidades": [
                {
                    "especialidad_id": clinica_id,
                    "duracion_turno_minutos": 45,
                }
            ]
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["especialidades"] == [
        {
            "especialidad_id": clinica_id,
            "duracion_turno_minutos": 45,
        }
    ]


def test_bloquea_quitar_especialidad_con_prestacion(client):
    autenticar_como("administrador")
    profesional, clinica_id, cardiologia_id = (
        crear_profesional_con_dos_especialidades(
            client
        )
    )
    crear_prestacion(
        client,
        profesional["id"],
        cardiologia_id,
    )

    respuesta = client.patch(
        f"/profesionales/{profesional['id']}",
        json={
            "especialidades": [
                {
                    "especialidad_id": clinica_id,
                    "duracion_turno_minutos": 45,
                }
            ]
        },
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == (
        "No se puede quitar la especialidad "
        "'Cardiología' porque tiene prestaciones "
        "asociadas a este profesional."
    )


def test_fallo_al_quitar_especialidad_es_atomico(client):
    autenticar_como("administrador")
    profesional, clinica_id, cardiologia_id = (
        crear_profesional_con_dos_especialidades(
            client
        )
    )
    crear_prestacion(
        client,
        profesional["id"],
        cardiologia_id,
    )

    respuesta = client.patch(
        f"/profesionales/{profesional['id']}",
        json={
            "nombre": "Nombre modificado",
            "especialidades": [
                {
                    "especialidad_id": clinica_id,
                    "duracion_turno_minutos": 60,
                }
            ],
        },
    )

    assert respuesta.status_code == 409

    consulta = client.get(
        f"/profesionales/{profesional['id']}"
    )
    datos = consulta.json()
    assert datos["nombre"] == "Ana"
    assert datos["especialidades"] == [
        {
            "especialidad_id": clinica_id,
            "duracion_turno_minutos": 45,
        },
        {
            "especialidad_id": cardiologia_id,
            "duracion_turno_minutos": 40,
        },
    ]
