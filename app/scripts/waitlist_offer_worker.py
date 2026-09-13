"""Expira ofertas waitlist; la creación de la siguiente oferta es explícita y segura."""
import logging
import signal
import time
from threading import Event
from datetime import datetime, timezone
from app.core.worker_config import load_worker_settings
from app.database.worker_connection import create_worker_session_factory
from app.services.waitlist_automation_service import expire_waitlist_offers, process_released_slot_waitlist
from app.services.waitlist_service import ReleasedSlot

logger = logging.getLogger("mediturnos.waitlist_worker")
SessionLocal = None
stop_event = Event()

def process_once(db, now=None):
    expired = expire_waitlist_offers(db, now or datetime.now(timezone.utc))
    for offer in expired:
        process_released_slot_waitlist(db, ReleasedSlot(offer.profesional_id, offer.prestacion_id, offer.slot_inicio, offer.slot_fin))
    return len(expired)

def run_forever(config, session_factory=None, sleeper=time.sleep, stop=stop_event):
    factory = session_factory or create_worker_session_factory(config)
    while not stop.is_set():
        db = factory()
        try:
            process_once(db)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("waitlist_worker.iteration_failed")
        finally:
            db.close()
        stop.wait(config.waitlist_offer_worker_interval_seconds)

def main() -> int:
    config = load_worker_settings()
    def shutdown(signum, frame):
        logger.info("waitlist_worker.shutdown signal=%s", signum)
        stop_event.set()
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    run_forever(config, session_factory=SessionLocal or None)
    return 0

if __name__ == "__main__": raise SystemExit(main())
