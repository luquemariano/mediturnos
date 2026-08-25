from datetime import UTC, datetime, timedelta

from app.models.study_request import StudyRequest
from app.services.study_access_token_service import create_study_access_token
from tests.test_study_requests import auth, cleanup, scenario


def test_profesional_genera_link_y_publica_minimo(client):
    db, user, _, professional, _, patient, _, _ = scenario()
    request = StudyRequest(paciente_id=patient.id, profesional_id=professional.id, title="Hemograma", instructions="En ayunas", status="pending", requested_at=datetime.now(UTC), created_at=datetime.now(UTC), updated_at=datetime.now(UTC))
    db.add(request); db.commit(); auth(user)
    response = client.post(f"/pacientes/{patient.id}/study-requests/{request.id}/access-link")
    assert response.status_code == 200
    token = response.json()["url"].split("token=", 1)[1]
    public = client.get("/public/study-requests/access", params={"token": token})
    assert public.status_code == 200
    assert public.headers["cache-control"] == "no-store"
    assert public.headers["referrer-policy"] == "no-referrer"
    body = public.json()
    assert body["title"] == "Hemograma"
    assert set(body) == {"study_request_id", "professional_name", "title", "instructions", "requested_at", "expires_at", "status"}
    for forbidden in ("patient_id", "paciente_id", "profesional_id", "turno_id", "email", "dni", "documents", "storage_key", "updated_at"):
        assert forbidden not in body
    cleanup(db)


def test_publico_rechaza_cancelada_y_no_enumera(client):
    db, _, _, professional, _, patient, _, _ = scenario()
    request = StudyRequest(paciente_id=patient.id, profesional_id=professional.id, title="Cancelada", status="cancelled", requested_at=datetime.now(UTC), created_at=datetime.now(UTC), updated_at=datetime.now(UTC))
    db.add(request); db.commit()
    token = create_study_access_token(secret="turnelia-local-study-access-secret", study_request_id=request.id, patient_id=patient.id)
    response = client.get("/public/study-requests/access", params={"token": token})
    assert response.status_code == 404
    assert response.json()["detail"] == "El enlace no es válido o ya no está disponible."
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"
    cleanup(db)


def test_publico_rechaza_patient_mismatch_y_request_inexistente(client):
    db, _, _, professional, _, patient, _, other_patient = scenario()
    request = StudyRequest(paciente_id=patient.id, profesional_id=professional.id, title="Privada", status="pending", requested_at=datetime.now(UTC), created_at=datetime.now(UTC), updated_at=datetime.now(UTC))
    db.add(request); db.commit()
    mismatch = create_study_access_token(secret="turnelia-local-study-access-secret", study_request_id=request.id, patient_id=other_patient.id)
    nonexistent = create_study_access_token(secret="turnelia-local-study-access-secret", study_request_id=999999, patient_id=patient.id)
    for token in (mismatch, nonexistent, "not-a-token"):
        response = client.get("/public/study-requests/access", params={"token": token})
        assert response.status_code == 404
        assert response.json()["detail"] == "El enlace no es válido o ya no está disponible."
    cleanup(db)


def test_publico_revoca_todos_los_estados_no_pending(client):
    db, _, _, professional, _, patient, _, _ = scenario()
    for status in ("cancelled", "closed", "submitted", "reviewed"):
        request = StudyRequest(paciente_id=patient.id, profesional_id=professional.id, title=status, status=status, requested_at=datetime.now(UTC), created_at=datetime.now(UTC), updated_at=datetime.now(UTC))
        db.add(request); db.flush()
        token = create_study_access_token(secret="turnelia-local-study-access-secret", study_request_id=request.id, patient_id=patient.id)
        assert client.get("/public/study-requests/access", params={"token": token}).status_code == 404
    cleanup(db)
