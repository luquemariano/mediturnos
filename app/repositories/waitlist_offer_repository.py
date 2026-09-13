from sqlalchemy.orm import Session
from datetime import datetime
from app.models.waitlist_offer import WaitlistOffer

def create(db: Session, **values):
    item = WaitlistOffer(**values); db.add(item); db.flush(); return item
def get_by_token_hash(db: Session, token_hash: str):
    query = db.query(WaitlistOffer).filter(WaitlistOffer.token_hash == token_hash)
    if db.get_bind().dialect.name == "postgresql":
        query = query.with_for_update(of=WaitlistOffer)
    return query.first()
def get_active_for_entry(db: Session, entry_id: int):
    return db.query(WaitlistOffer).filter(WaitlistOffer.waitlist_entry_id == entry_id, WaitlistOffer.estado == "activa").first()
def get_active_for_slot(db: Session, profesional_id: int, prestacion_id: int, slot_inicio):
    return db.query(WaitlistOffer).filter(WaitlistOffer.profesional_id == profesional_id, WaitlistOffer.prestacion_id == prestacion_id, WaitlistOffer.slot_inicio == slot_inicio, WaitlistOffer.estado == "activa").first()

def has_prior_offer_for_slot(db: Session, entry_id: int, slot_inicio, slot_fin):
    return db.query(WaitlistOffer).filter(WaitlistOffer.waitlist_entry_id == entry_id, WaitlistOffer.slot_inicio == slot_inicio, WaitlistOffer.slot_fin == slot_fin).first() is not None

def list_expired_active(db: Session, now: datetime, limit: int = 50):
    query = (db.query(WaitlistOffer)
            .filter(WaitlistOffer.estado == "activa", WaitlistOffer.expires_at <= now)
            .order_by(WaitlistOffer.expires_at, WaitlistOffer.id).limit(limit))
    if db.get_bind().dialect.name == "postgresql":
        query = query.with_for_update(skip_locked=True, of=WaitlistOffer)
    return query.all()
