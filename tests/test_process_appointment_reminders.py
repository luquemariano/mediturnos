from datetime import UTC, datetime

from app.scripts import process_appointment_reminders as script


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


def test_main_devuelve_codigo_no_cero_y_cierra_sesion(monkeypatch):
    db = DbFalsa()
    monkeypatch.setattr(script, "SessionLocal", lambda: db)
    monkeypatch.setattr(script, "process_once", lambda db: (_ for _ in ()).throw(RuntimeError("db")))
    assert script.main() == 1
    assert db.closed is True
