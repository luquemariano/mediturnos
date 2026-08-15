from datetime import datetime, timedelta, timezone

import pytest

from app.core.dependencies import obtener_usuario_actual
from app.main import app
from app.models.evolucion_clinica import EvolucionClinica
from app.models.paciente import Paciente
from app.models.profesional import Profesional
from app.models.profesional_paciente import ProfesionalPaciente
from app.models.usuario import Usuario
from tests.conftest import SessionTest


@pytest.fixture
def escenario_evoluciones():
    db = SessionTest()
    usuarios = {
        rol: Usuario(nombre=rol.title(), email=f"{rol}@evoluciones.test", password_hash="hash", rol=rol)
        for rol in ("profesional", "recepcionista", "paciente", "administrador")
    }
    usuario_ajeno = Usuario(nombre="Profesional ajeno", email="ajeno@evoluciones.test", password_hash="hash", rol="profesional")
    db.add_all([*usuarios.values(), usuario_ajeno]); db.flush()
    profesional = Profesional(usuario_id=usuarios["profesional"].id, nombre="Sofía", apellido="Rodríguez", matricula="EVO-1")
    profesional_ajeno = Profesional(usuario_id=usuario_ajeno.id, nombre="Bruno", apellido="Suárez", matricula="EVO-2")
    propio = Paciente(nombre="Ana", apellido="Propia", activo=True)
    ajeno = Paciente(nombre="Berta", apellido="Ajena", activo=True)
    db.add_all([profesional, profesional_ajeno, propio, ajeno]); db.flush()
    db.add_all([
        ProfesionalPaciente(profesional_id=profesional.id, paciente_id=propio.id),
        ProfesionalPaciente(profesional_id=profesional_ajeno.id, paciente_id=ajeno.id),
    ])
    ahora = datetime.now(timezone.utc)
    db.add_all([
        EvolucionClinica(paciente_id=propio.id, profesional_id=profesional.id, contenido="Registro anterior", created_at=ahora - timedelta(days=2)),
        EvolucionClinica(paciente_id=propio.id, profesional_id=profesional.id, contenido="Registro reciente", created_at=ahora),
    ])
    db.commit()
    datos = {**usuarios, "usuario_ajeno": usuario_ajeno, "profesional_modelo": profesional, "propio": propio, "ajeno": ajeno}
    yield datos
    app.dependency_overrides.pop(obtener_usuario_actual, None)
    db.close()


def autenticar(usuario):
    app.dependency_overrides[obtener_usuario_actual] = lambda: usuario


def test_profesional_obtiene_evoluciones_propias_ordenadas(client, escenario_evoluciones):
    autenticar(escenario_evoluciones["profesional"])
    respuesta = client.get(f'/pacientes/{escenario_evoluciones["propio"].id}/evoluciones')
    assert respuesta.status_code == 200
    assert [item["contenido"] for item in respuesta.json()] == ["Registro reciente", "Registro anterior"]
    assert respuesta.json()[0]["profesional_nombre"] == "Sofía Rodríguez"


def test_profesional_crea_evolucion_con_autor_de_sesion(client, escenario_evoluciones):
    autenticar(escenario_evoluciones["profesional"])
    respuesta = client.post(f'/pacientes/{escenario_evoluciones["propio"].id}/evoluciones', json={"contenido": "  Evolución nueva  ", "profesional_id": 999})
    assert respuesta.status_code == 201
    assert respuesta.json()["contenido"] == "Evolución nueva"
    assert respuesta.json()["profesional_id"] == escenario_evoluciones["profesional_modelo"].id


@pytest.mark.parametrize("metodo", ["get", "post"])
def test_profesional_no_accede_ni_crea_para_paciente_ajeno(client, escenario_evoluciones, metodo):
    autenticar(escenario_evoluciones["profesional"])
    respuesta = getattr(client, metodo)(f'/pacientes/{escenario_evoluciones["ajeno"].id}/evoluciones', **({"json": {"contenido": "No permitida"}} if metodo == "post" else {}))
    assert respuesta.status_code == 404


@pytest.mark.parametrize("rol", ["recepcionista", "paciente"])
@pytest.mark.parametrize("metodo", ["get", "post"])
def test_roles_sin_acceso_clinico_son_rechazados(client, escenario_evoluciones, rol, metodo):
    autenticar(escenario_evoluciones[rol])
    respuesta = getattr(client, metodo)(f'/pacientes/{escenario_evoluciones["propio"].id}/evoluciones', **({"json": {"contenido": "No permitida"}} if metodo == "post" else {}))
    assert respuesta.status_code == 403


@pytest.mark.parametrize("contenido", ["", "   \n\t"])
def test_contenido_vacio_es_rechazado(client, escenario_evoluciones, contenido):
    autenticar(escenario_evoluciones["profesional"])
    respuesta = client.post(f'/pacientes/{escenario_evoluciones["propio"].id}/evoluciones', json={"contenido": contenido})
    assert respuesta.status_code == 422


def test_administrador_puede_consultar_pero_no_crear(client, escenario_evoluciones):
    autenticar(escenario_evoluciones["administrador"])
    ruta = f'/pacientes/{escenario_evoluciones["propio"].id}/evoluciones'
    assert client.get(ruta).status_code == 200
    assert client.post(ruta, json={"contenido": "No permitida"}).status_code == 403
