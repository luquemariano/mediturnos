"""Procesa recordatorios de turnos; la lógica de negocio vive en el servicio."""

from dataclasses import dataclass
import logging
from datetime import datetime

from app.core.datetime_utils import ahora_utc
from app.core.worker_config import load_worker_settings
from app.database.worker_connection import create_worker_session_factory
from app.services.appointment_reminder_service import (
    claim_due_reminders,
    generate_upcoming_reminders,
    recover_stale_processing,
    send_claimed_reminder,
)

logger = logging.getLogger("mediturnos.appointment_reminders")
BATCH_SIZE = 50
SessionLocal = None


@dataclass
class ProcessingSummary:
    generated: int = 0
    recovered: int = 0
    claimed: int = 0
    sent: int = 0
    retried: int = 0
    failed: int = 0
    skipped: int = 0


def process_once(db, ahora: datetime | None = None, config=None) -> ProcessingSummary:
    ahora = ahora or ahora_utc()
    resumen = ProcessingSummary()
    logger.info("appointment_reminders.start")

    resumen.recovered = recover_stale_processing(db, ahora)
    creados = generate_upcoming_reminders(db, ahora)
    resumen.generated = len(creados)
    reclamados = claim_due_reminders(db, ahora, BATCH_SIZE)
    resumen.claimed = len(reclamados)

    logger.info("appointment_reminders.generated count=%d", resumen.generated)
    logger.info("appointment_reminders.claimed count=%d", resumen.claimed)
    for reminder in reclamados:
        try:
            if config is None:
                resultado = send_claimed_reminder(db, reminder, ahora)
            else:
                resultado = send_claimed_reminder(db, reminder, ahora, config=config)
            if resultado == "sent":
                resumen.sent += 1
            elif resultado == "pending":
                resumen.retried += 1
            elif resultado == "failed":
                resumen.failed += 1
            elif resultado == "skipped":
                resumen.skipped += 1
        except Exception:
            db.rollback()
            logger.exception("appointment_reminders.item_failed")
            resumen.failed += 1

    logger.info(
        "appointment_reminders.finished sent=%d retried=%d failed=%d skipped=%d",
        resumen.sent, resumen.retried, resumen.failed, resumen.skipped,
    )
    return resumen


def main() -> int:
    config = load_worker_settings()
    logger.info(
        "appointment_reminders.config database_configured=%s email_provider=%s timezone=%s",
        bool(config.database_url), config.email_provider, config.app_timezone,
    )
    db = (SessionLocal or create_worker_session_factory(config))()
    try:
        process_once(db, config=config)
        return 0
    except Exception:
        db.rollback()
        logger.exception("appointment_reminders.global_failed")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
