from datetime import datetime, timezone
from types import SimpleNamespace

from app.services import study_email_service
from app.services.email_service import EmailDeliveryError, EmailDeliveryResult


class Provider:
    def __init__(self, fail=False): self.messages = []; self.fail = fail
    def enviar(self, message):
        if self.fail: raise EmailDeliveryError("fallo controlado")
        self.messages.append(message); return EmailDeliveryResult("fake", "id")


def request():
    patient = SimpleNamespace(id=7, paciente_id=7, nombre="Ana", apellido="Pérez", email="ana@example.com")
    professional = SimpleNamespace(nombre="Dra.", apellido="López", email="dra@example.com", usuario=None)
    return SimpleNamespace(id=3, paciente_id=7, title="Hemograma", instructions="En ayunas", expires_at=None, paciente=patient, profesional=professional)


def test_new_request_email_uses_secure_link_without_extra_pii(monkeypatch):
    provider = Provider(); monkeypatch.setattr(study_email_service, "obtener_email_provider", lambda: provider)
    assert study_email_service.notify_new_request(request()) is True
    message = provider.messages[0]; assert message.destinatario == "ana@example.com"; assert "/estudios/enviar?token=" in message.texto; assert "Hemograma" in message.texto; assert "DNI" not in message.texto


def test_submit_email_contains_count_without_documents_or_tokens(monkeypatch):
    provider = Provider(); monkeypatch.setattr(study_email_service, "obtener_email_provider", lambda: provider)
    assert study_email_service.notify_results_submitted(request(), 2, datetime.now(timezone.utc)) is True
    message = provider.messages[0]; assert message.destinatario == "dra@example.com"; assert "2 archivo(s)" in message.texto; assert "storage_key" not in message.texto; assert "token=" not in message.texto


def test_review_email_is_a_privacy_safe_notification(monkeypatch):
    provider = Provider(); monkeypatch.setattr(study_email_service, "obtener_email_provider", lambda: provider)
    review = SimpleNamespace(study_request=request(), disposition="requires_in_person", review_text="sacar nuevo turno")
    assert study_email_service.notify_review_created(review) is True
    message = provider.messages[0]
    assert "revisó los resultados" in message.texto
    assert "revisó los resultados" in message.html
    assert "sacar nuevo turno" not in message.texto
    assert "sacar nuevo turno" not in message.html


def test_review_email_never_includes_sensitive_clinical_text(monkeypatch):
    provider = Provider(); monkeypatch.setattr(study_email_service, "obtener_email_provider", lambda: provider)
    sensitive = "Diagnóstico QA sensible que no debe enviarse por correo"
    review = SimpleNamespace(study_request=request(), disposition="online_response", review_text=sensitive)
    assert study_email_service.notify_review_created(review) is True
    message = provider.messages[0]
    assert sensitive not in message.texto
    assert sensitive not in message.html


def test_provider_failure_does_not_escape(monkeypatch):
    monkeypatch.setattr(study_email_service, "obtener_email_provider", lambda: Provider(fail=True))
    assert study_email_service.notify_new_request(request()) is False
    assert study_email_service.notify_results_submitted(request(), 1, datetime.now(timezone.utc)) is False
    assert study_email_service.notify_review_created(SimpleNamespace(study_request=request(), disposition="online_response", review_text="privado")) is False


def test_missing_recipient_skips_provider(monkeypatch):
    provider = Provider(); monkeypatch.setattr(study_email_service, "obtener_email_provider", lambda: provider)
    no_email = request(); no_email.paciente.email = None; assert study_email_service.notify_new_request(no_email) is False; assert provider.messages == []


def test_missing_professional_email_skips_results_notification(monkeypatch):
    provider = Provider(); monkeypatch.setattr(study_email_service, "obtener_email_provider", lambda: provider)
    no_email = request(); no_email.profesional.email = None; assert study_email_service.notify_results_submitted(no_email, 1, datetime.now(timezone.utc)) is False; assert provider.messages == []


def test_subjects_do_not_contain_patient_or_clinical_pii(monkeypatch):
    provider = Provider(); monkeypatch.setattr(study_email_service, "obtener_email_provider", lambda: provider)
    item = request(); assert study_email_service.notify_new_request(item) is True
    message = provider.messages[0]; assert "Ana" not in message.asunto; assert "Hemograma" not in message.asunto; assert "DNI" not in message.asunto
