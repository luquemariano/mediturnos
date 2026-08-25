from app.core.dependencies import obtener_usuario_actual
from app.integrations.storage.fake import FakeObjectStorageProvider
from app.integrations.storage.base import StoredObjectMetadata
from app.main import app
from app.models.paciente import Paciente
from app.models.patient_document import PatientDocument
from app.models.profesional import Profesional
from app.models.profesional_paciente import ProfesionalPaciente
from app.models.usuario import Usuario
from tests.conftest import SessionTest
import pytest

def escenario():
    db = SessionTest(); usuario = Usuario(nombre="Profesional", email="docs-prof@test", password_hash="hash", rol="profesional"); db.add(usuario); db.flush()
    profesional = Profesional(usuario_id=usuario.id, nombre="Doc", apellido="Tor", matricula="DOC-1"); paciente = Paciente(nombre="Paciente", apellido="Doc", activo=True); ajeno = Paciente(nombre="Ajeno", apellido="Doc", activo=True); db.add_all([profesional, paciente, ajeno]); db.flush(); db.add(ProfesionalPaciente(profesional_id=profesional.id, paciente_id=paciente.id)); db.commit(); return db, usuario, profesional, paciente, ajeno

def autenticar(usuario): app.dependency_overrides[obtener_usuario_actual] = lambda: usuario

def test_intent_confirm_list_download_and_soft_delete(client, monkeypatch):
    db, usuario, profesional, paciente, _ = escenario(); storage = FakeObjectStorageProvider(); monkeypatch.setattr("app.services.patient_document_service._provider", lambda: storage); autenticar(usuario)
    ruta = f"/pacientes/{paciente.id}/documents"
    respuesta = client.post(f"{ruta}/upload-intents", json={"filename": "../../laboratorio.pdf", "mime_type": "application/pdf", "size_bytes": 12, "category": "laboratory"})
    assert respuesta.status_code == 201; intent = respuesta.json(); documento = db.query(PatientDocument).one(); assert documento.original_filename == "laboratorio.pdf"; assert "patient_id" not in documento.storage_key
    storage.register_object(documento.storage_key, 12, "application/pdf")
    assert client.post(f"{ruta}/{intent['document_id']}/confirm").json()["status"] == "available"
    assert client.get(ruta).json()[0]["original_filename"] == "laboratorio.pdf"
    assert client.post(f"{ruta}/{intent['document_id']}/download-url").status_code == 200
    assert client.delete(f"{ruta}/{intent['document_id']}").json()["status"] == "deleted"
    assert client.get(ruta).json() == []
    app.dependency_overrides.pop(obtener_usuario_actual, None); db.close()

def test_invalid_mime_size_and_foreign_patient_are_rejected(client, monkeypatch):
    db, usuario, _, paciente, ajeno = escenario(); monkeypatch.setattr("app.services.patient_document_service._provider", lambda: FakeObjectStorageProvider()); autenticar(usuario)
    base = {"filename": "x.pdf", "mime_type": "application/pdf", "size_bytes": 1, "category": "other"}
    assert client.post(f"/pacientes/{paciente.id}/documents/upload-intents", json={**base, "mime_type": "text/plain"}).status_code == 422
    assert client.post(f"/pacientes/{paciente.id}/documents/upload-intents", json={**base, "size_bytes": 0}).status_code == 422
    assert client.post(f"/pacientes/{ajeno.id}/documents/upload-intents", json=base).status_code == 404
    app.dependency_overrides.pop(obtener_usuario_actual, None); db.close()

def test_confirm_mismatched_head_fails_and_does_not_list(client, monkeypatch):
    db, usuario, _, paciente, _ = escenario(); storage = FakeObjectStorageProvider(); monkeypatch.setattr("app.services.patient_document_service._provider", lambda: storage); autenticar(usuario)
    ruta = f"/pacientes/{paciente.id}/documents"; intent = client.post(f"{ruta}/upload-intents", json={"filename": "x.pdf", "mime_type": "application/pdf", "size_bytes": 10, "category": "report"}).json(); documento = db.query(PatientDocument).one(); storage.register_object(documento.storage_key, 11, "application/pdf")
    assert client.post(f"{ruta}/{intent['document_id']}/confirm").status_code == 422; assert client.get(ruta).json() == []
    app.dependency_overrides.pop(obtener_usuario_actual, None); db.close()

def test_pending_and_failed_are_not_listed_and_double_confirm_is_idempotent(client, monkeypatch):
    db, usuario, _, paciente, _ = escenario(); storage = FakeObjectStorageProvider(); monkeypatch.setattr("app.services.patient_document_service._provider", lambda: storage); autenticar(usuario); ruta = f"/pacientes/{paciente.id}/documents"
    intent = client.post(f"{ruta}/upload-intents", json={"filename": "x.png", "mime_type": "image/png", "size_bytes": 3, "category": "imaging"}).json(); assert client.get(ruta).json() == []
    documento = db.query(PatientDocument).one(); storage.register_object(documento.storage_key, 3, "image/png"); assert client.post(f"{ruta}/{intent['document_id']}/confirm").json()["status"] == "available"; assert client.post(f"{ruta}/{intent['document_id']}/confirm").json()["status"] == "available"
    app.dependency_overrides.pop(obtener_usuario_actual, None); db.close()

def test_document_ownership_applies_to_confirm_download_and_delete(client, monkeypatch):
    db, usuario, _, paciente, ajeno = escenario(); storage = FakeObjectStorageProvider(); monkeypatch.setattr("app.services.patient_document_service._provider", lambda: storage); autenticar(usuario)
    intent = client.post(f"/pacientes/{paciente.id}/documents/upload-intents", json={"filename": "x.pdf", "mime_type": "application/pdf", "size_bytes": 3, "category": "report"}).json(); documento = db.query(PatientDocument).one(); storage.register_object(documento.storage_key, 3, "application/pdf"); client.post(f"/pacientes/{paciente.id}/documents/{documento.id}/confirm")
    for method, path in (("post", "confirm"), ("post", "download-url"), ("delete", "delete")):
        response = getattr(client, method)(f"/pacientes/{ajeno.id}/documents/{documento.id}/{path}" if path != "delete" else f"/pacientes/{ajeno.id}/documents/{documento.id}")
        assert response.status_code == 404
    app.dependency_overrides.pop(obtener_usuario_actual, None); db.close()

def test_roles_are_restricted_and_admin_can_read(client, monkeypatch):
    db, usuario, _, paciente, _ = escenario(); storage = FakeObjectStorageProvider(); monkeypatch.setattr("app.services.patient_document_service._provider", lambda: storage); autenticar(usuario); ruta = f"/pacientes/{paciente.id}/documents"; intent = client.post(f"{ruta}/upload-intents", json={"filename": "x.pdf", "mime_type": "application/pdf", "size_bytes": 3, "category": "report"}).json(); documento = db.query(PatientDocument).one(); storage.register_object(documento.storage_key, 3, "application/pdf"); client.post(f"{ruta}/{documento.id}/confirm")
    admin = Usuario(nombre="Admin", email="admin-doc@test", password_hash="hash", rol="administrador"); reception = Usuario(nombre="Recepción", email="recep-doc@test", password_hash="hash", rol="recepcionista"); patient = Usuario(nombre="Paciente", email="patient-doc@test", password_hash="hash", rol="paciente"); db.add_all([admin, reception, patient]); db.commit()
    autenticar(admin); assert client.get(ruta).status_code == 200; assert client.post(f"{ruta}/upload-intents", json={"filename": "x.pdf", "mime_type": "application/pdf", "size_bytes": 3, "category": "report"}).status_code == 403
    for restricted in (reception, patient): autenticar(restricted); assert client.get(ruta).status_code == 403
    app.dependency_overrides.pop(obtener_usuario_actual, None); db.close()

@pytest.mark.parametrize("mime_type", ["image/jpeg", "image/png", "image/webp"])
def test_supported_image_mimes_and_exact_limit(client, monkeypatch, mime_type):
    db, usuario, _, paciente, _ = escenario(); monkeypatch.setattr("app.services.patient_document_service._provider", lambda: FakeObjectStorageProvider()); autenticar(usuario); base = {"filename": "x", "mime_type": mime_type, "size_bytes": 10 * 1024 * 1024, "category": "other"}
    assert client.post(f"/pacientes/{paciente.id}/documents/upload-intents", json=base).status_code == 201
    assert client.post(f"/pacientes/{paciente.id}/documents/upload-intents", json={**base, "size_bytes": 10 * 1024 * 1024 + 1}).status_code == 422
    app.dependency_overrides.pop(obtener_usuario_actual, None); db.close()
