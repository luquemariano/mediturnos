import pytest

from app.core.dependencies import obtener_usuario_actual
from app.main import app
from app.models.usuario import Usuario


@pytest.fixture(autouse=True)
def autenticar_administrador():
    administrador = Usuario(
        id=1,
        nombre="Administrador",
        email="admin@example.com",
        password_hash="hash",
        rol="administrador",
        activo=True,
    )
    app.dependency_overrides[
        obtener_usuario_actual
    ] = lambda: administrador

    yield

    app.dependency_overrides.pop(
        obtener_usuario_actual,
        None,
    )


def test_prestacion_inexistente_devuelve_404(client):
    respuesta = client.get("/prestaciones/999999")

    assert respuesta.status_code == 404
    assert respuesta.json() == {
        "detail": "Prestación no encontrada."
    }


def test_crear_prestacion_correctamente(client):
    respuesta_especialidad = client.post(
        "/especialidades/",
        json={
            "nombre": "Cardiología",
            "descripcion": "Atención cardiovascular",
            "duracion_turno_minutos": 30,
        },
    )

    assert respuesta_especialidad.status_code == 201

    especialidad_id = respuesta_especialidad.json()["id"]

    respuesta_profesional = client.post(
        "/profesionales/",
        json={
            "nombre": "Ana",
            "apellido": "Gómez",
            "matricula": "MP-TEST-001",
            "telefono": "3515551234",
            "email": "ana.test@mediturnos.com",
            "especialidades": [
                {
                    "especialidad_id": especialidad_id,
                    "duracion_turno_minutos": 30,
                }
            ],
        },
    )

    assert respuesta_profesional.status_code == 201

    profesional_id = respuesta_profesional.json()["id"]

    respuesta_prestacion = client.post(
        "/prestaciones/",
        json={
            "nombre": "Consulta inicial",
            "descripcion": "Primera evaluación cardiológica",
            "duracion_minutos": 40,
            "precio": "35000.00",
            "modalidad": "presencial",
            "profesional_id": profesional_id,
            "especialidad_id": especialidad_id,
        },
    )

    assert respuesta_prestacion.status_code == 201

    datos = respuesta_prestacion.json()

    assert datos["nombre"] == "Consulta inicial"
    assert datos["duracion_minutos"] == 40
    assert datos["precio"] == "35000.00"
    assert datos["modalidad"] == "presencial"
    assert datos["activa"] is True
    assert datos["profesional_id"] == profesional_id
    assert datos["especialidad_id"] == especialidad_id
