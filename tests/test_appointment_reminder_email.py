from datetime import UTC, datetime

from app.services import email_service


def test_recordatorio_texto_html_y_timezone():
    mensaje = email_service.construir_email_recordatorio_turno(
        "persona@example.com",
        "Juan",
        "Dra. Sofía Ramírez",
        "Cardiología",
        "Consulta",
        datetime(2026, 8, 20, 18, 30, tzinfo=UTC),
    )
    assert mensaje.asunto == "Recordatorio de tu turno — Turnelia"
    for contenido in (mensaje.texto, mensaje.html):
        assert "Juan" in contenido
        assert "Dra. Sofía Ramírez" in contenido
        assert "Cardiología" in contenido
        assert "Consulta" in contenido
        assert "20/08/2026" in contenido
        assert "15:30" in contenido


def test_recordatorio_escapa_html_y_omite_prestacion():
    mensaje = email_service.construir_email_recordatorio_turno(
        "persona@example.com", "Juan <script>alert(1)</script>", "Profesional",
        "Especialidad", None, datetime(2026, 8, 20, 18, 30, tzinfo=UTC),
    )
    assert "<script>" not in mensaje.html
    assert "&lt;script&gt;" in mensaje.html
    assert "Prestación" not in mensaje.texto
    assert "Prestación" not in mensaje.html


def test_inmemory_provider_devuelve_resultado_y_no_hace_http():
    email_service.development_email_outbox.clear()
    resultado = email_service.InMemoryEmailProvider().enviar(
        email_service.TransactionalEmail("persona@example.com", "A", "<p>H</p>", "T")
    )
    assert resultado.provider == "in_memory"
    assert resultado.message_id is None
    assert email_service.development_email_outbox["persona@example.com"] == "T"
