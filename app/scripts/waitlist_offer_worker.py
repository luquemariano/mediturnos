"""Expira ofertas waitlist; la creación de la siguiente oferta es explícita y segura."""
import logging
from datetime import datetime, timezone
from app.core.worker_config import load_worker_settings
from app.database.worker_connection import create_worker_session_factory
from app.services.waitlist_automation_service import expire_waitlist_offers, process_released_slot_waitlist
from app.services.waitlist_service import ReleasedSlot

logger = logging.getLogger("mediturnos.waitlist_worker")
SessionLocal = None

def process_once(db, now=None):
    expired = expire_waitlist_offers(db, now or datetime.now(timezone.utc))
    for offer in expired:
        process_released_slot_waitlist(db, ReleasedSlot(offer.profesional_id, offer.prestacion_id, offer.slot_inicio, offer.slot_fin))
    return len(expired)

def main() -> int:
    config = load_worker_settings()
    db = (SessionLocal or create_worker_session_factory(config))()
    try:
        process_once(db); return 0
    except Exception:
        db.rollback(); logger.exception("waitlist_worker.failed"); return 1
    finally: db.close()

if __name__ == "__main__": raise SystemExit(main())
