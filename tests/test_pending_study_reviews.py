from datetime import datetime, timedelta, timezone

import pytest

from app.core.dependencies import obtener_usuario_actual
from app.main import app
from app.models.patient_document import PatientDocument
from app.models.study_request import StudyRequest
from app.models.usuario import Usuario
from tests.test_study_requests import cleanup, scenario, auth

def add_request(db, professional, patient, status, submitted_at):
    request = StudyRequest(paciente_id=patient.id, profesional_id=professional.id, title=f"Estudio {status}", status=status, requested_at=submitted_at - timedelta(days=1), submitted_at=submitted_at if status == "submitted" else None, created_at=submitted_at, updated_at=submitted_at)
    db.add(request); db.commit(); return request

def add_document(db, patient, request, status="available", origin="patient"):
    document = PatientDocument(paciente_id=patient.id, study_request_id=request.id, origin=origin, storage_key=f"patient-documents/{request.id}-{status}-{origin}.pdf", original_filename="resultado.pdf", mime_type="application/pdf", size_bytes=10, category="study_result", status=status)
    db.add(document); db.commit(); return document

def test_pending_review_filters_orders_counts_and_isolates_professional(client):
    db, user, other_user, professional, other, patient, _, other_patient = scenario(); now = datetime.now(timezone.utc)
    old = add_request(db, professional, patient, "submitted", now - timedelta(days=2)); current = add_request(db, professional, patient, "submitted", now - timedelta(days=1)); other_professional_request = add_request(db, other, patient, "submitted", now - timedelta(days=3)); add_request(db, professional, patient, "pending", now); add_request(db, professional, patient, "reviewed", now); add_document(db, patient, old); add_document(db, patient, old, "pending_upload"); add_document(db, patient, old, "failed"); add_document(db, patient, old, "deleted"); add_document(db, patient, old, "available", "professional"); add_document(db, other_patient, current)
    auth(user); response = client.get("/profesionales/me/study-requests/pending-review"); assert response.status_code == 200; body = response.json(); assert body["count"] == 2; assert [item["id"] for item in body["items"]] == [old.id, current.id]; assert body["items"][0]["documents_count"] == 1; assert set(body["items"][0]) == {"id", "paciente_id", "patient_name", "title", "requested_at", "submitted_at", "documents_count"}; auth(other_user); assert [item["id"] for item in client.get("/profesionales/me/study-requests/pending-review").json()["items"]] == [other_professional_request.id]; cleanup(db)

def test_pending_review_keeps_submitted_request_without_documents(client):
    db, user, _, professional, _, patient, _, _ = scenario(); request = add_request(db, professional, patient, "submitted", datetime.now(timezone.utc)); auth(user); body = client.get("/profesionales/me/study-requests/pending-review").json(); assert body["count"] == 1; assert body["items"][0]["id"] == request.id; assert body["items"][0]["documents_count"] == 0; cleanup(db)

@pytest.mark.parametrize("role", ["administrador", "recepcionista", "paciente"])
def test_pending_review_is_professional_only(client, role):
    db, _, _, professional, _, patient, _, _ = scenario(); user = Usuario(nombre=role, email=f"{role}-pending@test", password_hash="hash", rol=role); db.add(user); db.commit(); add_request(db, professional, patient, "submitted", datetime.now(timezone.utc)); auth(user); assert client.get("/profesionales/me/study-requests/pending-review").status_code == 403; cleanup(db)
