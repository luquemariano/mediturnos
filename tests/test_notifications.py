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
    def release(items, entity_id):
        return [item for item in items if item.type == "product_release" and item.entity_type == "product_update" and item.entity_id == entity_id]
    first = release(items, 127); second = release(items, 128)
    assert len(first) == 1 and len(second) == 1 and unread == 2
    assert first[0].title == "Nueva función: Lista de espera inteligente"
    assert second[0].title == "Nuevo: compartí tu página de reservas"
    assert "Paciente" not in first[0].message and "Paciente" not in second[0].message
    other_items, other_unread = list_notifications(db, other_user.id)
    assert len(release(other_items, 127)) == 1 and len(release(other_items, 128)) == 1 and other_unread == 2
    assert {item.user_id for item in first + second} == {user.id}
    assert {item.user_id for item in release(other_items, 127) + release(other_items, 128)} == {other_user.id}
    from app.services.notification_service import mark_notification_read
    mark_notification_read(db, user.id, first[0].id)
    items_after, unread_after = list_notifications(db, user.id)
    assert release(items_after, 127)[0].read_at is not None
    assert release(items_after, 128)[0].read_at is None and unread_after == 1
    mark_notification_read(db, user.id, second[0].id)
    items_final, unread_final = list_notifications(db, user.id)
    assert release(items_final, 127)[0].read_at is not None and release(items_final, 128)[0].read_at is not None and unread_final == 0
    assert len(release(items_final, 127)) == 1 and len(release(items_final, 128)) == 1
