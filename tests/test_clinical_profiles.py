import pytest
from app.core.dependencies import obtener_usuario_actual
from app.main import app
from app.models.clinical_profile import ClinicalProfile
from app.models.paciente import Paciente
from app.models.profesional import Profesional
from app.models.profesional_paciente import ProfesionalPaciente
from app.models.usuario import Usuario
from tests.conftest import SessionTest


@pytest.fixture
def escenario_clinico(client):
    db = SessionTest()
    usuarios = {rol: Usuario(nombre=rol, email=f"{rol}@clinical.test", password_hash="hash", rol=("profesional" if rol == "ajeno" else rol)) for rol in ("profesional", "ajeno", "recepcionista", "paciente", "administrador")}
    db.add_all(usuarios.values()); db.flush()
    profesional = Profesional(usuario_id=usuarios["profesional"].id, nombre="Pro", apellido="Uno", matricula="C-1")
    ajeno = Profesional(usuario_id=usuarios["ajeno"].id, nombre="Pro", apellido="Dos", matricula="C-2")
    paciente = Paciente(nombre="Paciente", apellido="Propio", activo=True)
    otro = Paciente(nombre="Paciente", apellido="Ajeno", activo=True)
    db.add_all([profesional, ajeno, paciente, otro]); db.flush()
    db.add_all([ProfesionalPaciente(profesional_id=profesional.id, paciente_id=paciente.id), ProfesionalPaciente(profesional_id=ajeno.id, paciente_id=otro.id)])
    db.commit()
    yield usuarios, profesional, paciente, otro
    app.dependency_overrides.pop(obtener_usuario_actual, None); db.close()


def autenticar(usuario): app.dependency_overrides[obtener_usuario_actual] = lambda: usuario


def test_profesional_crea_actualiza_y_no_duplica(client, escenario_clinico):
    usuarios, profesional, paciente, _ = escenario_clinico; autenticar(usuarios["profesional"])
    ruta = f"/pacientes/{paciente.id}/clinical-profile"
    assert client.get(ruta).json()["id"] is None
    respuesta = client.put(ruta, json={"antecedentes": "  Asma  ", "alergias": ""})
    assert respuesta.status_code == 200 and respuesta.json()["antecedentes"] == "Asma"
    respuesta = client.put(ruta, json={"observaciones": "Control"})
    assert respuesta.status_code == 200
    db = SessionTest(); assert db.query(ClinicalProfile).filter_by(paciente_id=paciente.id).count() == 1; db.close()


@pytest.mark.parametrize("rol", ["recepcionista", "paciente"])
def test_roles_no_clinicos_reciben_403(client, escenario_clinico, rol):
    usuarios, _, paciente, _ = escenario_clinico; autenticar(usuarios[rol])
    assert client.get(f"/pacientes/{paciente.id}/clinical-profile").status_code == 403
    assert client.put(f"/pacientes/{paciente.id}/clinical-profile", json={}).status_code == 403


def test_profesional_ajeno_no_accede_y_admin_solo_lee(client, escenario_clinico):
    usuarios, _, paciente, _ = escenario_clinico; autenticar(usuarios["ajeno"])
    assert client.get(f"/pacientes/{paciente.id}/clinical-profile").status_code == 404
    autenticar(usuarios["administrador"])
    assert client.get(f"/pacientes/{paciente.id}/clinical-profile").status_code == 200
    assert client.put(f"/pacientes/{paciente.id}/clinical-profile", json={}).status_code == 403
