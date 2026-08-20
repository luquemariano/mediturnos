from datetime import datetime, timedelta, timezone
import pytest
from app.core.dependencies import obtener_usuario_actual
from app.main import app
from app.models.paciente import Paciente
from app.models.profesional import Profesional
from app.models.profesional_paciente import ProfesionalPaciente
from app.models.study_request import StudyRequest
from app.models.usuario import Usuario
from tests.conftest import SessionTest

def scenario():
    db = SessionTest(); user = Usuario(nombre="Profesional", email="study-prof@test", password_hash="hash", rol="profesional"); other_user = Usuario(nombre="Otro", email="study-other@test", password_hash="hash", rol="profesional"); db.add_all([user, other_user]); db.flush(); professional = Profesional(usuario_id=user.id, nombre="Pro", apellido="Uno", matricula="ST-1"); other = Profesional(usuario_id=other_user.id, nombre="Pro", apellido="Dos", matricula="ST-2"); patient = Paciente(nombre="Paciente", apellido="Study", activo=True); inactive = Paciente(nombre="Inactivo", apellido="Study", activo=False); other_patient = Paciente(nombre="Ajeno", apellido="Study", activo=True); db.add_all([professional, other, patient, inactive, other_patient]); db.flush(); db.add_all([ProfesionalPaciente(profesional_id=professional.id, paciente_id=patient.id), ProfesionalPaciente(profesional_id=other.id, paciente_id=other_patient.id)]); db.commit(); return db, user, other_user, professional, other, patient, inactive, other_patient
def auth(user): app.dependency_overrides[obtener_usuario_actual] = lambda: user
def cleanup(db): app.dependency_overrides.pop(obtener_usuario_actual, None); db.close()

def test_create_normalizes_and_validates_expiration(client):
    db, user, _, professional, _, patient, _, _ = scenario(); auth(user); route = f"/pacientes/{patient.id}/study-requests"; response = client.post(route, json={"title": "  Hemograma completo  ", "instructions": "  En ayunas.  ", "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()}); assert response.status_code == 201; body = response.json(); assert body["title"] == "Hemograma completo"; assert body["instructions"] == "En ayunas."; assert body["status"] == "pending"; assert body["profesional_id"] == professional.id; cleanup(db)

def test_create_rejects_invalid_access_and_expiration(client):
    db, user, other_user, _, _, patient, inactive, other_patient = scenario(); route = f"/pacientes/{patient.id}/study-requests"; auth(other_user); assert client.post(route, json={"title": "Estudio"}).status_code == 404; auth(user); assert client.post(f"/pacientes/{inactive.id}/study-requests", json={"title": "Estudio"}).status_code == 404; assert client.post(f"/pacientes/{patient.id}/study-requests", json={"title": " ", "expires_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()}).status_code == 422; assert client.post(f"/pacientes/{other_patient.id}/study-requests", json={"title": "Estudio"}).status_code == 404; cleanup(db)

def test_list_detail_and_ownership(client):
    db, user, other_user, professional, other, patient, _, other_patient = scenario(); request = StudyRequest(paciente_id=patient.id, profesional_id=professional.id, title="Primero", status="pending", requested_at=datetime.now(timezone.utc) - timedelta(days=1), created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)); db.add(request); db.commit(); auth(user); route = f"/pacientes/{patient.id}/study-requests"; assert client.get(route).status_code == 200; assert client.get(f"{route}/{request.id}").status_code == 200; auth(other_user); assert client.get(f"/pacientes/{patient.id}/study-requests/{request.id}").status_code == 404; cleanup(db)

def test_cancel_and_close_are_owner_only_and_idempotent(client):
    db, user, other_user, professional, other, patient, _, _ = scenario(); request = StudyRequest(paciente_id=patient.id, profesional_id=professional.id, title="Cancelar", status="pending", requested_at=datetime.now(timezone.utc), created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)); closed = StudyRequest(paciente_id=patient.id, profesional_id=professional.id, title="Cerrar", status="pending", requested_at=datetime.now(timezone.utc), created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)); db.add_all([request, closed]); db.commit(); auth(other_user); assert client.post(f"/pacientes/{patient.id}/study-requests/{request.id}/cancel").status_code == 404; auth(user); assert client.post(f"/pacientes/{patient.id}/study-requests/{request.id}/cancel").json()["status"] == "cancelled"; assert client.post(f"/pacientes/{patient.id}/study-requests/{request.id}/cancel").json()["status"] == "cancelled"; assert client.post(f"/pacientes/{patient.id}/study-requests/{closed.id}/close").json()["status"] == "closed"; assert client.post(f"/pacientes/{patient.id}/study-requests/{closed.id}/close").json()["status"] == "closed"; cleanup(db)

def test_cancelled_cannot_close_and_closed_cannot_cancel(client):
    db, user, _, professional, _, patient, _, _ = scenario(); now = datetime.now(timezone.utc); cancelled = StudyRequest(paciente_id=patient.id, profesional_id=professional.id, title="Cancelada", status="cancelled", requested_at=now, created_at=now, updated_at=now); closed = StudyRequest(paciente_id=patient.id, profesional_id=professional.id, title="Cerrada", status="closed", requested_at=now, created_at=now, updated_at=now); db.add_all([cancelled, closed]); db.commit(); auth(user); assert client.post(f"/pacientes/{patient.id}/study-requests/{cancelled.id}/close").status_code == 409; assert client.post(f"/pacientes/{patient.id}/study-requests/{closed.id}/cancel").status_code == 409; cleanup(db)

@pytest.mark.parametrize("role", ["administrador", "recepcionista", "paciente"])
def test_non_professional_create_is_forbidden(client, role):
    db, _, _, _, _, patient, _, _ = scenario(); user = Usuario(nombre=role, email=f"{role}-study@test", password_hash="hash", rol=role); db.add(user); db.commit(); auth(user); assert client.post(f"/pacientes/{patient.id}/study-requests", json={"title": "Estudio"}).status_code == 403; cleanup(db)
