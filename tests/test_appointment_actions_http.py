from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import app
from app.services.appointment_action_token_service import generate_appointment_action_token


def test_email_scanner_gets_do_not_mutate_appointment(monkeypatch):
    token_confirm = generate_appointment_action_token(secret="turnelia-local-appointment-action-secret", turno_id=123, appointment_datetime_snapshot=datetime.now(UTC), action_scope="confirm")
    token_cancel = generate_appointment_action_token(secret="turnelia-local-appointment-action-secret", turno_id=123, appointment_datetime_snapshot=datetime.now(UTC), action_scope="cancel")
    with TestClient(app) as client:
        for path, token in (("confirmar", token_confirm), ("cancelar", token_cancel), ("confirmar", token_confirm), ("cancelar", token_cancel)):
            response = client.get(f"/turnos/public/{path}", params={"token": token})
            assert response.status_code == 200
            assert "<form method='post'" in response.text
            assert "confirmado correctamente" not in response.text
            assert "cancelado correctamente" not in response.text
