from sqlalchemy.orm import Session, joinedload
from app.models.waitlist_offer import WaitlistOffer
from app.models.waitlist_entry import WaitlistEntry

def create(db: Session, **values):
    item = WaitlistOffer(**values); db.add(item); db.flush(); return item
def get_by_token_hash(db: Session, token_hash: str):
    return db.query(WaitlistOffer).options(joinedload(WaitlistOffer.entry).joinedload(WaitlistEntry.paciente), joinedload(WaitlistOffer.entry).joinedload(WaitlistEntry.prestacion), joinedload(WaitlistOffer.entry).joinedload(WaitlistEntry.profesional)).filter(WaitlistOffer.token_hash == token_hash).with_for_update().first()
def get_active_for_entry(db: Session, entry_id: int):
    return db.query(WaitlistOffer).filter(WaitlistOffer.waitlist_entry_id == entry_id, WaitlistOffer.estado == "activa").first()
def get_active_for_slot(db: Session, profesional_id: int, prestacion_id: int, slot_inicio):
    return db.query(WaitlistOffer).filter(WaitlistOffer.profesional_id == profesional_id, WaitlistOffer.prestacion_id == prestacion_id, WaitlistOffer.slot_inicio == slot_inicio, WaitlistOffer.estado == "activa").first()
