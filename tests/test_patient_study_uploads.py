from datetime import UTC, datetime, timedelta

import pytest

from app.integrations.storage.fake import FakeObjectStorageProvider
from app.models.patient_document import PatientDocument
from app.models.study_request import StudyRequest
from app.services.study_access_token_service import create_study_access_token
from tests.test_study_requests import cleanup, scenario

SECRET = "turnelia-local-study-access-secret"

def make_request(db, professional, patient, status="pending", expires_at=None):
    request = StudyRequest(paciente_id=patient.id, profesional_id=professional.id, title="Resultado", status=status, expires_at=expires_at, requested_at=datetime.now(UTC), created_at=datetime.now(UTC), updated_at=datetime.now(UTC)); db.add(request); db.commit(); return request

def test_intent_confirm_submit_y_no_expone_storage_key(client, monkeypatch):
    db, _, _, professional, _, patient, _, _ = scenario(); request = make_request(db, professional, patient); token = create_study_access_token(secret=SECRET, study_request_id=request.id, patient_id=patient.id); provider = FakeObjectStorageProvider(); monkeypatch.setattr("app.services.public_study_upload_service.factory.get_object_storage_provider", lambda: provider)
    intent = client.post("/public/study-requests/upload-intents", json={"token": token, "filename": "../resultado.pdf", "mime_type": "application/pdf", "size_bytes": 120}); assert intent.status_code == 200; body = intent.json(); assert set(body) == {"document_id", "upload_url", "expires_in_seconds", "required_content_type"}; document = db.get(PatientDocument, body["document_id"]); assert document.origin == "patient"; assert document.category == "study_result"; assert document.uploaded_by_profesional_id is None; assert document.study_request_id == request.id; assert "storage_key" not in body
    provider.register_object(document.storage_key, 120, "application/pdf"); confirmed = client.post(f"/public/study-requests/documents/{document.id}/confirm", json={"token": token}); assert confirmed.status_code == 200; assert confirmed.json()["status"] == "available"; submitted = client.post("/public/study-requests/submit", json={"token": token}); assert submitted.status_code == 200; assert submitted.json()["status"] == "submitted"; cleanup(db)

def test_rechaza_mime_tamano_limite_y_submit_sin_available(client):
    db, _, _, professional, _, patient, _, _ = scenario(); request = make_request(db, professional, patient); token = create_study_access_token(secret=SECRET, study_request_id=request.id, patient_id=patient.id)
    assert client.post("/public/study-requests/upload-intents", json={"token": token, "filename": "x.exe", "mime_type": "application/x-msdownload", "size_bytes": 1}).status_code == 422
    assert client.post("/public/study-requests/upload-intents", json={"token": token, "filename": "x.pdf", "mime_type": "application/pdf", "size_bytes": 10 * 1024 * 1024 + 1}).status_code == 422
    assert client.post("/public/study-requests/submit", json={"token": token}).status_code == 409; cleanup(db)

def test_pending_upload_bloquea_submit_y_remove_hace_soft_delete(client, monkeypatch):
    db, _, _, professional, _, patient, _, _ = scenario(); request = make_request(db, professional, patient); token = create_study_access_token(secret=SECRET, study_request_id=request.id, patient_id=patient.id); provider = FakeObjectStorageProvider(); monkeypatch.setattr("app.services.public_study_upload_service.factory.get_object_storage_provider", lambda: provider); intent = client.post("/public/study-requests/upload-intents", json={"token": token, "filename": "x.png", "mime_type": "image/png", "size_bytes": 20}).json(); assert client.post("/public/study-requests/submit", json={"token": token}).status_code == 409; removed = client.post(f"/public/study-requests/documents/{intent['document_id']}/remove", json={"token": token}); assert removed.status_code == 200; assert db.get(PatientDocument, intent["document_id"]).status == "deleted"; cleanup(db)

def test_token_no_puede_operar_documento_de_otra_request(client, monkeypatch):
    db, _, _, professional, _, patient, _, _ = scenario(); first = make_request(db, professional, patient); second = make_request(db, professional, patient); document = PatientDocument(paciente_id=patient.id, study_request_id=second.id, origin="patient", storage_key="patient-documents/other.pdf", original_filename="other.pdf", mime_type="application/pdf", size_bytes=10, category="study_result", status="pending_upload"); db.add(document); db.commit(); token = create_study_access_token(secret=SECRET, study_request_id=first.id, patient_id=patient.id); assert client.post(f"/public/study-requests/documents/{document.id}/remove", json={"token": token}).status_code == 404; cleanup(db)

@pytest.mark.parametrize("status", ["cancelled", "closed", "submitted", "reviewed"])
def test_request_no_pending_rechaza_intent(client, status):
    db, _, _, professional, _, patient, _, _ = scenario(); request = make_request(db, professional, patient, status=status); token = create_study_access_token(secret=SECRET, study_request_id=request.id, patient_id=patient.id); assert client.post("/public/study-requests/upload-intents", json={"token": token, "filename": "x.pdf", "mime_type": "application/pdf", "size_bytes": 10}).status_code == 404; cleanup(db)
