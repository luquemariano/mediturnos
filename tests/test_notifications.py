from datetime import datetime, timezone

from app.models.notification import Notification
from app.services.notification_service import list_notifications
from tests.test_study_requests import auth, cleanup, scenario


def test_notifications_are_isolated_and_readable(client):
    db, user, other_user, professional, other_professional, patient, _, _ = scenario()
    first = Notification(user_id=user.id, type="study_results_submitted", title="Resultados", message="Paciente QA envió resultados", entity_type="study_request", entity_id=7, created_at=datetime.now(timezone.utc))
    other = Notification(user_id=other_user.id, type="study_results_submitted", title="Otro", message="No corresponde", entity_type="study_request", entity_id=8, created_at=datetime.now(timezone.utc))
    db.add_all([first, other]); db.commit()
    auth(user)
    response = client.get("/notifications")
    assert response.status_code == 200
    payload = response.json()
    assert payload["unread_count"] == sum(item["read_at"] is None for item in payload["items"])
    assert any(item["type"] == "study_results_submitted" and item["message"] == "Paciente QA envió resultados" for item in payload["items"])
    assert any(item["type"] == "product_release" and item["entity_type"] == "product_update" and item["entity_id"] == 127 for item in payload["items"])
    assert client.post(f"/notifications/{first.id}/read").status_code == 200
    assert client.get("/notifications").json()["unread_count"] == payload["unread_count"] - 1
    auth(other_user)
    assert client.post(f"/notifications/{first.id}/read").status_code == 404
    cleanup(db)


def test_product_release_is_idempotent_per_professional():
    db, user, other_user, professional, other_professional, patient, _, _ = scenario()
    user.rol = "profesional"; other_user.rol = "profesional"; db.commit()
    list_notifications(db, user.id); list_notifications(db, user.id); list_notifications(db, other_user.id)
    items, unread = list_notifications(db, user.id)
    product = [item for item in items if item.type == "product_release"]
    assert len(product) == 1 and unread == 1
    assert product[0].entity_type == "product_update" and product[0].entity_id == 127
    assert product[0].title == "Nueva función: Lista de espera inteligente"
    assert "Paciente" not in product[0].message
    assert len([item for item in list_notifications(db, other_user.id)[0] if item.type == "product_release"]) == 1
    from app.services.notification_service import mark_notification_read
    mark_notification_read(db, user.id, product[0].id)
    items_after, unread_after = list_notifications(db, user.id)
    product_after = next(item for item in items_after if item.type == "product_release")
    assert product_after.read_at is not None and unread_after == 0
