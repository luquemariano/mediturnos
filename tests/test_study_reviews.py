from datetime import datetime, timezone

import pytest

from app.models.evolucion_clinica import EvolucionClinica
from app.models.patient_document import PatientDocument
from app.models.study_request import StudyRequest
from app.models.study_review import StudyReview
from tests.test_study_requests import auth, cleanup, scenario


def submitted(db, professional, patient, status="submitted"):
    request = StudyRequest(paciente_id=patient.id, profesional_id=professional.id, title="Resonancia", status=status, requested_at=datetime.now(timezone.utc), submitted_at=datetime.now(timezone.utc) if status == "submitted" else None)
    db.add(request); db.commit(); return request


def document(db, patient, request, origin="patient", status="available"):
    value = PatientDocument(paciente_id=patient.id, study_request_id=request.id, origin=origin, storage_key=f"review-{request.id}-{origin}-{status}", original_filename="resultado.pdf", mime_type="application/pdf", size_bytes=10, category="study_result", status=status)
    db.add(value); db.commit(); return value


def post(client, user, patient, request, payload=None):
    auth(user); return client.post(f"/pacientes/{patient.id}/study-requests/{request.id}/review", json=payload or {"review_text": "Resultado compatible.", "disposition": "online_response"})


def test_creates_review_transaction_and_short_evolution(client):
    db, user, _, professional, _, patient, _, _ = scenario(); request = submitted(db, professional, patient); document(db, patient, request)
    response = post(client, user, patient, request); assert response.status_code == 201; db.refresh(request)
    review = db.query(StudyReview).one(); evolution = db.query(EvolucionClinica).filter_by(study_review_id=review.id).one()
    assert request.status == "reviewed" and request.reviewed_at is not None; assert evolution.tipo == "study_review"; assert evolution.study_review_id == review.id; assert "Resultado compatible" not in evolution.contenido
    cleanup(db)


def test_review_requires_owner_and_patient_document(client):
    db, user, other_user, professional, other, patient, _, _ = scenario(); request = submitted(db, professional, patient); auth(other_user); assert client.post(f"/pacientes/{patient.id}/study-requests/{request.id}/review", json={"review_text": "x", "disposition": "online_response"}).status_code in (403, 404); document(db, patient, request, origin="professional"); auth(user); assert post(client, user, patient, request).status_code == 409; cleanup(db)


@pytest.mark.parametrize("status", ["pending", "reviewed", "closed", "cancelled"])
def test_only_submitted_can_be_reviewed(client, status):
    db, user, _, professional, _, patient, _, _ = scenario(); request = submitted(db, professional, patient, status); document(db, patient, request); assert post(client, user, patient, request).status_code == 409; cleanup(db)


@pytest.mark.parametrize("payload", [{"review_text": "", "disposition": "online_response"}, {"review_text": "x", "disposition": "invalid"}, {"review_text": "x", "disposition": "online_response", "status": "reviewed"}])
def test_payload_validation_and_spoofing(client, payload):
    db, user, _, professional, _, patient, _, _ = scenario(); request = submitted(db, professional, patient); document(db, patient, request); response = post(client, user, patient, request, payload); assert response.status_code == 422; cleanup(db)


def test_double_review_and_get(client):
    db, user, _, professional, _, patient, _, _ = scenario(); request = submitted(db, professional, patient); document(db, patient, request); assert post(client, user, patient, request).status_code == 201; assert post(client, user, patient, request).status_code == 409; auth(user); assert client.get(f"/pacientes/{patient.id}/study-requests/{request.id}/review").status_code == 200; assert db.query(StudyReview).count() == 1; cleanup(db)
