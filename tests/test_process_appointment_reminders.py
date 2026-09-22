from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from pydantic import SecretStr
from sqlalchemy.sql import operators

from app.integrations.messaging import FakeMessagingProvider
from app.models.message_delivery import MessageDelivery
from app.models.turno import Turno
from app.scripts import process_appointment_reminders as script
from app.services import appointment_reminder_service
from tests.conftest import SessionTest


def _turno_whatsapp(turno_id, fecha_hora, *, estado="reservado", opt_in=True,
                    telefono="0351 15 1234567", email=None):
    return SimpleNamespace(
        id=turno_id,
        fecha_hora=fecha_hora,
        estado=estado,
        paciente=SimpleNamespace(
            whatsapp_opt_in=opt_in,
            whatsapp_opt_out_at=None,
            telefono=telefono,
            email=email or f"paciente{turno_id}@example.test",
        ),
        profesional=SimpleNamespace(nombre="Profesional", apellido="Prueba"),
        prestacion=SimpleNamespace(
            nombre="Consulta",
            especialidad=SimpleNamespace(nombre="Especialidad"),
        ),
    )


def _ejecutar_worker_whatsapp(monkeypatch, turnos, ahora, *, enabled=True, provider=None):
    db = SessionTest()
    real_get = db.get
    por_id = {turno.id: turno for turno in turnos}
    db.get = lambda model, item_id: por_id.get(item_id) if model is Turno else real_get(model, item_id)
    query_real = db.query

    class QueryTurnos:
        def __init__(self):
            self.criteria = ()

        def filter(self, *criteria):
            self.criteria = criteria
            return self

        def all(self):
            def matches(turno):
                for criterion in self.criteria:
                    field = criterion.left.key
                    value = criterion.right.value
                    actual = getattr(turno, field)
                    if criterion.operator is operators.in_op and actual not in value:
                        return False
                    if criterion.operator is operators.gt and not actual > value:
                        return False
                    if criterion.operator is operators.le and not actual <= value:
                        return False
                return True

            return [turno for turno in turnos if matches(turno)]

    def query(model, *args, **kwargs):
        return QueryTurnos() if model is Turno else query_real(model, *args, **kwargs)

    db.query = query
    emails = []

    class EmailProvider:
        def enviar(self, message):
            emails.append(message)
            return SimpleNamespace(provider="test", message_id=f"email-{len(emails)}")

    def make_reminder(turno):
        return SimpleNamespace(
            turno_id=turno.id,
            status="processing",
            appointment_datetime_snapshot=turno.fecha_hora,
            recipient_email_snapshot=turno.paciente.email,
            patient_name_snapshot="Paciente Prueba",
            professional_name_snapshot="Profesional Prueba",
            specialty_name_snapshot="Especialidad",
            service_name_snapshot="Consulta",
            attempt_count=0,
            processing_started_at=ahora,
        )

    reminders = [make_reminder(turno) for turno in turnos]

    original_config = SimpleNamespace(
        whatsapp_enabled=enabled,
        whatsapp_provider="fake",
        public_api_url="https://api.example.test",
        appointment_action_secret=SecretStr("wa7-test-secret"),
        email_provider="resend",
        resend_api_key=SecretStr("test-key"),
        email_from="test@example.test",
        app_timezone="America/Argentina/Buenos_Aires",
    )
    monkeypatch.setattr(script, "generate_upcoming_reminders", lambda *_args: [])
    monkeypatch.setattr(script, "claim_due_reminders", lambda *_args: reminders)
    monkeypatch.setattr(script, "recover_stale_processing", lambda *_args: 0)
    monkeypatch.setattr(appointment_reminder_service, "obtener_email_provider", lambda *_args: EmailProvider())
    summary = script.process_once(
        db, ahora, config=original_config,
        whatsapp_provider=provider or FakeMessagingProvider(),
    )
    return summary, db, emails


class DbFalsa:
    def __init__(self):
        self.rollbacks = 0
        self.closed = False

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def test_process_once_orquesta_flujo_y_resume(monkeypatch):
    llamadas = []
    monkeypatch.setattr(script, "recover_stale_processing", lambda db, ahora: 2)
    monkeypatch.setattr(script, "generate_upcoming_reminders", lambda db, ahora: [1, 2])
    monkeypatch.setattr(script, "claim_due_reminders", lambda db, ahora, limite: [1, 2, 3])

    def enviar(db, reminder, ahora):
        llamadas.append(reminder)
        return {1: "sent", 2: "pending", 3: "failed"}[reminder]

    monkeypatch.setattr(script, "send_claimed_reminder", enviar)
    resumen = script.process_once(DbFalsa(), datetime.now(UTC))
    assert resumen.generated == 2
    assert resumen.recovered == 2
    assert resumen.claimed == 3
    assert resumen.sent == 1
    assert resumen.retried == 1
    assert resumen.failed == 1
    assert llamadas == [1, 2, 3]


def test_process_once_continua_si_un_reminder_falla(monkeypatch):
    db = DbFalsa()
    monkeypatch.setattr(script, "recover_stale_processing", lambda *args: 0)
    monkeypatch.setattr(script, "generate_upcoming_reminders", lambda *args: [])
    monkeypatch.setattr(script, "claim_due_reminders", lambda *args: [1, 2])

    def enviar(db, reminder, ahora):
        if reminder == 1:
            raise RuntimeError("fallo controlado")
        return "sent"

    monkeypatch.setattr(script, "send_claimed_reminder", enviar)
    resumen = script.process_once(db, datetime.now(UTC))
    assert resumen.sent == 1
    assert resumen.failed == 1
    assert db.rollbacks == 1


def test_worker_whatsapp_envia_si_target_ya_ocurrio_y_sigue_en_ventana(monkeypatch):
    ahora = datetime(2026, 9, 22, 12, 15, tzinfo=UTC)
    turno = _turno_whatsapp(201, ahora + timedelta(hours=23, minutes=31))
    provider = FakeMessagingProvider()

    summary, db, emails = _ejecutar_worker_whatsapp(monkeypatch, [turno], ahora, provider=provider)

    assert summary.whatsapp_sent == 1
    assert summary.whatsapp_failed == summary.whatsapp_skipped == 0
    assert len(provider.sent_messages) == 1
    assert len(emails) == 1
    db.close()


def test_worker_whatsapp_respeta_ambos_limites_de_ventana(monkeypatch):
    ahora = datetime(2026, 9, 22, 12, 15, tzinfo=UTC)
    antes = _turno_whatsapp(202, ahora + timedelta(hours=24, minutes=1))
    limite_inicial = _turno_whatsapp(203, ahora + timedelta(hours=24))
    limite_final = _turno_whatsapp(204, ahora + timedelta(hours=23, minutes=30))
    provider = FakeMessagingProvider()

    summary, db, emails = _ejecutar_worker_whatsapp(
        monkeypatch, [antes, limite_inicial, limite_final], ahora, provider=provider,
    )

    assert summary.whatsapp_sent == 1
    assert len(provider.sent_messages) == 1
    assert len(emails) == 3
    assert summary.whatsapp_skipped == 0
    db.close()


def test_worker_ejecuciones_consecutivas_no_duplican_delivery(monkeypatch):
    ahora = datetime(2026, 9, 22, 12, 15, tzinfo=UTC)
    turno = _turno_whatsapp(205, ahora + timedelta(hours=23, minutes=50))
    provider = FakeMessagingProvider()
    summary, db, _emails = _ejecutar_worker_whatsapp(monkeypatch, [turno], ahora, provider=provider)

    second_summary = script.process_once(
        db, ahora + timedelta(minutes=5),
        config=SimpleNamespace(
            whatsapp_enabled=True,
            whatsapp_provider="fake",
            public_api_url="https://api.example.test",
            appointment_action_secret=SecretStr("wa7-test-secret"),
            email_provider="resend",
            resend_api_key=SecretStr("test-key"),
            email_from="test@example.test",
            app_timezone="America/Argentina/Buenos_Aires",
        ),
        whatsapp_provider=provider,
    )

    assert summary.whatsapp_sent == 1
    assert second_summary.whatsapp_sent == 0
    assert second_summary.whatsapp_skipped == 0
    assert db.query(MessageDelivery).filter(MessageDelivery.status == "sent").count() == 1
    assert len(provider.sent_messages) == 1
    db.close()


def test_worker_disabled_omite_whatsapp_y_envia_email(monkeypatch):
    ahora = datetime(2026, 9, 22, 12, 15, tzinfo=UTC)
    turno = _turno_whatsapp(206, ahora + timedelta(hours=23, minutes=50))
    provider = FakeMessagingProvider()

    summary, db, emails = _ejecutar_worker_whatsapp(
        monkeypatch, [turno], ahora, enabled=False, provider=provider,
    )

    assert summary.whatsapp_skipped == 1
    assert summary.whatsapp_sent == summary.whatsapp_failed == 0
    assert provider.sent_messages == []
    assert len(emails) == 1
    db.close()


def test_worker_sin_optin_o_telefono_valido_omite_wa_sin_perder_email(monkeypatch):
    ahora = datetime(2026, 9, 22, 12, 15, tzinfo=UTC)
    sin_optin = _turno_whatsapp(207, ahora + timedelta(hours=23, minutes=50), opt_in=False)
    telefono_invalido = _turno_whatsapp(208, ahora + timedelta(hours=23, minutes=50), telefono="123")
    provider = FakeMessagingProvider()

    summary, db, emails = _ejecutar_worker_whatsapp(
        monkeypatch, [sin_optin, telefono_invalido], ahora, provider=provider,
    )

    assert summary.whatsapp_skipped == 2
    assert summary.whatsapp_sent == summary.whatsapp_failed == 0
    assert provider.sent_messages == []
    assert len(emails) == 2
    db.close()


def test_worker_falla_wa_persiste_failed_continua_lote_y_envia_email(monkeypatch):
    ahora = datetime(2026, 9, 22, 12, 15, tzinfo=UTC)
    primero = _turno_whatsapp(209, ahora + timedelta(hours=23, minutes=50))
    segundo = _turno_whatsapp(210, ahora + timedelta(hours=23, minutes=55))
    provider = FakeMessagingProvider(fail_next=True)

    summary, db, emails = _ejecutar_worker_whatsapp(
        monkeypatch, [primero, segundo], ahora, provider=provider,
    )

    assert summary.whatsapp_failed == 1
    assert summary.whatsapp_sent == 1
    assert summary.failed == 0
    assert db.query(MessageDelivery).filter(MessageDelivery.status == "failed").count() == 1
    assert db.query(MessageDelivery).filter(MessageDelivery.status == "sent").count() == 1
    assert len(emails) == 2
    assert len(provider.sent_messages) == 1
    db.close()


def test_worker_no_considera_estados_no_notificables(monkeypatch):
    ahora = datetime(2026, 9, 22, 12, 15, tzinfo=UTC)
    turnos = [
        _turno_whatsapp(211 + index, ahora + timedelta(hours=23, minutes=50), estado=status)
        for index, status in enumerate(("cancelado", "finalizado", "ausente"))
    ]
    provider = FakeMessagingProvider()

    summary, db, emails = _ejecutar_worker_whatsapp(monkeypatch, turnos, ahora, provider=provider)

    assert summary.whatsapp_sent == summary.whatsapp_failed == summary.whatsapp_skipped == 0
    assert db.query(MessageDelivery).count() == 0
    assert provider.sent_messages == []
    assert len(emails) == 0
    db.close()


def test_worker_reprogramado_en_ventana_crea_nueva_idempotency_key(monkeypatch):
    ahora = datetime(2026, 9, 22, 12, 15, tzinfo=UTC)
    turno = _turno_whatsapp(214, ahora + timedelta(hours=23, minutes=50))
    provider = FakeMessagingProvider()
    summary, db, _emails = _ejecutar_worker_whatsapp(monkeypatch, [turno], ahora, provider=provider)
    first_key = db.query(MessageDelivery).one().idempotency_key

    nueva_ahora = ahora + timedelta(days=2)
    turno.fecha_hora = nueva_ahora + timedelta(hours=23, minutes=50)
    second_summary = script.process_once(
        db, nueva_ahora,
        config=SimpleNamespace(
            whatsapp_enabled=True,
            whatsapp_provider="fake",
            public_api_url="https://api.example.test",
            appointment_action_secret=SecretStr("wa7-test-secret"),
        ),
        whatsapp_provider=provider,
    )

    deliveries = db.query(MessageDelivery).order_by(MessageDelivery.id).all()
    assert summary.whatsapp_sent == second_summary.whatsapp_sent == 1
    assert len(deliveries) == 2
    assert deliveries[0].idempotency_key != deliveries[1].idempotency_key
    assert deliveries[0].idempotency_key == first_key
    assert len(provider.sent_messages) == 2
    db.close()


def test_worker_considera_instantes_aware_en_distintos_timezone(monkeypatch):
    ahora = datetime(2026, 9, 22, 15, 15, tzinfo=UTC)
    turno = _turno_whatsapp(
        215,
        datetime(2026, 9, 23, 12, 5, tzinfo=ZoneInfo("America/Argentina/Buenos_Aires")),
    )
    provider = FakeMessagingProvider()

    summary, db, _emails = _ejecutar_worker_whatsapp(monkeypatch, [turno], ahora, provider=provider)

    assert summary.whatsapp_sent == 1
    assert len(provider.sent_messages) == 1
    db.close()


def test_main_devuelve_codigo_no_cero_y_cierra_sesion(monkeypatch):
    db = DbFalsa()
    monkeypatch.setattr(script, "SessionLocal", lambda: db)
    monkeypatch.setattr(
        script,
        "load_worker_settings",
        lambda: SimpleNamespace(
            database_url="sqlite:///./worker-test.db",
            email_provider="in_memory",
            app_timezone="America/Argentina/Buenos_Aires",
        ),
    )
    monkeypatch.setattr(script, "process_once", lambda db: (_ for _ in ()).throw(RuntimeError("db")))
    assert script.main() == 1
    assert db.closed is True
