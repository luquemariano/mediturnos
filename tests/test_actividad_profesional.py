import pytest
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

from app.core.dependencies import obtener_usuario_actual
from app.main import app
from app.models.actividad_profesional import ActividadProfesional
from app.models.especialidad import Especialidad
from app.models.profesional import Profesional
from app.models.usuario import Usuario
from app.services.email_service import development_email_outbox
from tests.conftest import SessionTest


def _registrar(client, email: str, actividad_id: int, **datos):
    body = {
        "nombre": "Caso",
        "apellido": "Sintético",
        "email": email,
        "password": "secreto123",
        "actividad_profesional_id": actividad_id,
    }
    body.update(datos)
    return client.post("/auth/register/profesional", json=body)


def _autenticar(client, email: str, password: str = "secreto123"):
    token = parse_qs(urlparse(development_email_outbox[email].split("Verificar correo: ", 1)[1].splitlines()[0]).query)["token"][0]
    assert client.post("/auth/verify-email", json={"token": token}).status_code == 200
    respuesta = client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


@pytest.fixture(autouse=True)
def limpiar_override():
    yield
    app.dependency_overrides.pop(obtener_usuario_actual, None)


def _actividad(codigo: str) -> int:
    with SessionTest() as db:
        item = db.query(ActividadProfesional).filter_by(codigo=codigo).first()
        if item is None:
            if codigo == "servicios_estetica":
                specialty_name = "Estética"
                requires_license = False
                requires_specialty = False
            else:
                specialty_name = "Clínica actividad test"
                requires_license = True
                requires_specialty = True
            specialty = db.query(Especialidad).filter_by(nombre=specialty_name).first()
            if specialty is None:
                specialty = Especialidad(nombre=specialty_name, duracion_turno_minutos=30, activa=True)
                db.add(specialty); db.flush()
            item = ActividadProfesional(
                codigo=codigo,
                nombre="Servicios de estética" if not requires_license else "Actividad matriculable",
                requiere_matricula=requires_license,
                requiere_especialidad=requires_specialty,
                especialidad_predeterminada_id=specialty.id if not requires_specialty else None,
            )
            db.add(item); db.commit(); db.refresh(item)
        return item.id


def test_perfil_heredado_sin_actividad_conserva_matricula_y_edicion_basica(client):
    with SessionTest() as db:
        user = Usuario(nombre="Heredado", email="legacy-activity@example.test", password_hash="unused", rol="profesional", activo=True)
        db.add(user); db.flush()
        professional = Profesional(usuario_id=user.id, nombre="Perfil", apellido="Heredado", matricula="LEGACY-123", onboarding_step="completado")
        db.add(professional); db.commit(); profile_id = professional.id; user_id = user.id
    app.dependency_overrides[obtener_usuario_actual] = lambda: SimpleNamespace(id=user_id, rol="profesional")
    lectura = client.get("/profesionales/me")
    assert lectura.status_code == 200
    assert lectura.json()["actividad_profesional_id"] is None
    assert lectura.json()["matricula"] == "LEGACY-123"
    cambio = client.patch("/profesionales/me", json={"telefono": "111222333"})
    assert cambio.status_code == 200
    with SessionTest() as db:
        actual = db.get(Profesional, profile_id)
        assert actual.actividad_profesional_id is None
        assert actual.matricula == "LEGACY-123"


def test_profesional_no_puede_editar_perfil_ajeno_ni_anular_requisitos(client):
    matriculable_id = _actividad("profesional_matriculable")
    _actividad("profesional_matriculable")
    with SessionTest() as db:
        specialty_id = db.query(Especialidad.id).filter_by(nombre="Clínica actividad test").scalar()
    propio = _registrar(client, "own-activity@example.com", matriculable_id, matricula="MAT-OWN-123", especialidad_id=specialty_id)
    assert propio.status_code == 201
    own_headers = _autenticar(client, "own-activity@example.com")
    otro = _registrar(client, "other-activity@example.com", matriculable_id, matricula="MAT-OTHER-123", especialidad_id=specialty_id)
    assert otro.status_code == 201
    other_headers = _autenticar(client, "other-activity@example.com")
    own_id = propio.json()["profesional_id"]
    denied = client.patch(f"/profesionales/{own_id}", json={"actividad_profesional_id": matriculable_id, "matricula": "ALTERADA"}, headers=other_headers)
    assert denied.status_code == 403
    nulled = client.patch("/profesionales/me", json={"actividad_profesional_id": None}, headers=own_headers)
    assert nulled.status_code == 422
    no_matricula = client.patch("/profesionales/me", json={"matricula": "   "}, headers=own_headers)
    assert no_matricula.status_code == 422
    assert client.patch("/profesionales/me", json={"profesional_id": own_id, "actividad_profesional_id": matriculable_id}, headers=other_headers).status_code == 422
    with SessionTest() as db:
        target = db.get(Profesional, own_id)
        assert target.matricula == "MAT-OWN-123"
        assert target.actividad_profesional.codigo == "profesional_matriculable"


def test_clasificar_perfil_heredado_exige_limpiar_matricula_antes_de_estetica(client):
    estetica_id = _actividad("servicios_estetica")
    with SessionTest() as db:
        user = Usuario(nombre="Legacy", email="legacy-classify@example.com", password_hash="unused", rol="profesional", activo=True)
        db.add(user); db.flush()
        professional = Profesional(usuario_id=user.id, nombre="Legacy", apellido="Perfil", matricula="OLD-MAT-123", onboarding_step="completado")
        db.add(professional); db.commit(); professional_id = professional.id; user_id = user.id
    app.dependency_overrides[obtener_usuario_actual] = lambda: SimpleNamespace(id=user_id, rol="profesional")

    implicit_clear = client.patch("/profesionales/me", json={"actividad_profesional_id": estetica_id})
    assert implicit_clear.status_code == 422
    with SessionTest() as db:
        assert db.get(Profesional, professional_id).matricula == "OLD-MAT-123"

    explicit_clear = client.patch(
        "/profesionales/me",
        json={"actividad_profesional_id": estetica_id, "matricula": None},
    )
    assert explicit_clear.status_code == 200
    with SessionTest() as db:
        actual = db.get(Profesional, professional_id)
        assert actual.matricula is None
        assert actual.actividad_profesional.codigo == "servicios_estetica"
        assert [item.especialidad.nombre for item in actual.especialidades_asignadas] == ["Estética"]
