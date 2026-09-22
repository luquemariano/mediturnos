"""Procesa recordatorios de turnos; la lógica de negocio vive en el servicio."""

from dataclasses import dataclass
import logging
from datetime import datetime, timedelta

from app.core.datetime_utils import ahora_utc, desde_base_utc
from app.core.worker_config import load_worker_settings
from app.database.worker_connection import create_worker_session_factory
from app.integrations.messaging import MessagingProvider
from app.models.turno import Turno
from app.services.appointment_reminder_service import (
    claim_due_reminders,
    generate_upcoming_reminders,
    recover_stale_processing,
    send_claimed_reminder,
)
from app.services.whatsapp_appointment_reminder_service import (
    send_whatsapp_appointment_reminder,
)

logger = logging.getLogger("mediturnos.appointment_reminders")
BATCH_SIZE = 50
WHATSAPP_REMINDER_WINDOW = timedelta(minutes=30)
APPOINTMENT_REMINDER_LEAD_TIME = timedelta(hours=24)
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
    whatsapp_sent: int = 0
    whatsapp_failed: int = 0
    whatsapp_skipped: int = 0


def _whatsapp_turnos_en_ventana(db, ahora: datetime):
    """Devuelve turnos evaluables ahora; el borde final de 30m es exclusivo."""
    if not hasattr(db, "query"):
        return []
    ahora_utc = desde_base_utc(ahora)
    fin_turno = ahora_utc + APPOINTMENT_REMINDER_LEAD_TIME
    inicio_turno = fin_turno - WHATSAPP_REMINDER_WINDOW
    return (
        db.query(Turno)
        .filter(
            Turno.estado.in_({"reservado", "confirmado"}),
            Turno.fecha_hora > inicio_turno,
            Turno.fecha_hora <= fin_turno,
        )
        .all()
    )


def process_once(
    db,
    ahora: datetime | None = None,
    config=None,
    whatsapp_provider: MessagingProvider | None = None,
) -> ProcessingSummary:
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

    for turno in _whatsapp_turnos_en_ventana(db, ahora):
        try:
            resultado = send_whatsapp_appointment_reminder(
                db, turno.id, provider=whatsapp_provider, config=config, ahora=ahora,
            )
            if resultado.status == "sent":
                resumen.whatsapp_sent += 1
            elif resultado.status == "failed":
                resumen.whatsapp_failed += 1
            elif resultado.status in {"feature_disabled", "not_eligible"}:
                resumen.whatsapp_skipped += 1
            # already_sent/processing son resultados idempotentes en curso,
            # no fallos ni skips de elegibilidad/configuración.
        except Exception:
            db.rollback()
            logger.error("appointment_reminders.whatsapp_item_failed")
            resumen.whatsapp_failed += 1

    logger.info(
        "appointment_reminders.finished sent=%d retried=%d failed=%d skipped=%d whatsapp_sent=%d whatsapp_failed=%d whatsapp_skipped=%d",
        resumen.sent, resumen.retried, resumen.failed, resumen.skipped,
        resumen.whatsapp_sent, resumen.whatsapp_failed, resumen.whatsapp_skipped,
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
