from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session
from app.models.waitlist_offer import WaitlistOffer
from app.services.waitlist_service import ReleasedSlot, find_matching_waitlist_entries
from app.services.waitlist_offer_service import create_waitlist_offer
from app.services.email_service import enviar_email_oferta_waitlist, EmailDeliveryError
from app.repositories import waitlist_offer_repository as offer_repo

logger = logging.getLogger("mediturnos.waitlist_automation")

def process_released_slot_waitlist(db: Session, slot: ReleasedSlot):
    matches = find_matching_waitlist_entries(db, slot)
    if not matches:
        logger.info("waitlist_no_candidate profesional_id=%s prestacion_id=%s", slot.profesional_id, slot.prestacion_id)
        return "no_candidate"
    for entry in matches:
        if offer_repo.has_prior_offer_for_slot(db, entry.id, slot.fecha_hora, slot.fecha_fin):
            continue
        try:
            offer, token = create_waitlist_offer(db, entry, slot)
            try:
                enviar_email_oferta_waitlist(offer, token)
            except Exception:
                offer.estado = "cancelada"; entry.estado = "activa"; db.commit()
                logger.exception("waitlist_offer_notification_failed offer_id=%s waitlist_entry_id=%s", offer.id, entry.id)
                return "notification_failed"
            logger.info("waitlist_offer_notification_sent offer_id=%s waitlist_entry_id=%s", offer.id, entry.id)
            return "offered"
        except Exception:
            db.rollback()
            logger.exception("waitlist_offer_creation_failed profesional_id=%s prestacion_id=%s", slot.profesional_id, slot.prestacion_id)
            return "offer_failed"
    return "no_candidate"

def expire_waitlist_offers(db: Session, now: datetime | None = None, limit: int = 50):
    now = now or datetime.now(timezone.utc)
    expired = offer_repo.list_expired_active(db, now, limit)
    results = []
    for offer in expired:
        offer.estado = "vencida"
        if offer.entry.estado == "ofertada": offer.entry.estado = "activa"
        db.commit(); db.refresh(offer)
        logger.info("waitlist_offer_expired offer_id=%s waitlist_entry_id=%s", offer.id, offer.waitlist_entry_id)
        results.append(offer)
    return results
