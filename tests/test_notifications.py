from datetime import datetime, timezone

from app.models.notification import Notification
from tests.test_study_requests import auth, cleanup, scenario


def test_notifications_are_isolated_and_readable(client):
    db, user, other_user, professional, other_professional, patient, _, _ = scenario()
    first = Notification(user_id=user.id, type="study_results_submitted", title="Resultados", message="Paciente QA envió resultados", entity_type="study_request", entity_id=7, created_at=datetime.now(timezone.utc))
    other = Notification(user_id=other_user.id, type="study_results_submitted", title="Otro", message="No corresponde", entity_type="study_request", entity_id=8, created_at=datetime.now(timezone.utc))
    db.add_all([first, other]); db.commit()
    auth(user)
    response = client.get("/notifications")
    assert response.status_code == 200
    assert response.json()["unread_count"] == 1
    assert response.json()["items"][0]["message"] == "Paciente QA envió resultados"
    assert client.post(f"/notifications/{first.id}/read").status_code == 200
    assert client.get("/notifications").json()["unread_count"] == 0
    auth(other_user)
    assert client.post(f"/notifications/{first.id}/read").status_code == 404
    cleanup(db)
