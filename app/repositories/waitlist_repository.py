from datetime import date, time
from sqlalchemy.orm import Session, joinedload
from app.models.waitlist_entry import WaitlistEntry


def create(db: Session, **values) -> WaitlistEntry:
    item = WaitlistEntry(**values)
    db.add(item); db.flush()
    return item


def get_by_id(db: Session, entry_id: int, profesional_id: int) -> WaitlistEntry | None:
    return db.query(WaitlistEntry).options(joinedload(WaitlistEntry.paciente), joinedload(WaitlistEntry.prestacion)).filter(WaitlistEntry.id == entry_id, WaitlistEntry.profesional_id == profesional_id).first()


def get_by_public_id(db: Session, public_id: str, profesional_id: int) -> WaitlistEntry | None:
    return db.query(WaitlistEntry).filter(WaitlistEntry.identificador_publico == public_id, WaitlistEntry.profesional_id == profesional_id).first()


def list_by_profesional(db: Session, profesional_id: int, estado: str | None = None, prestacion_id: int | None = None) -> list[WaitlistEntry]:
    query = db.query(WaitlistEntry).options(joinedload(WaitlistEntry.paciente), joinedload(WaitlistEntry.prestacion)).filter(WaitlistEntry.profesional_id == profesional_id)
    if estado: query = query.filter(WaitlistEntry.estado == estado)
    if prestacion_id: query = query.filter(WaitlistEntry.prestacion_id == prestacion_id)
    return query.order_by(WaitlistEntry.created_at, WaitlistEntry.id).all()


def get_active_duplicate(db: Session, profesional_id: int, prestacion_id: int, paciente_id: int, fecha_desde: date, fecha_hasta: date, hora_desde: time | None, hora_hasta: time | None) -> WaitlistEntry | None:
    return db.query(WaitlistEntry).filter(WaitlistEntry.profesional_id == profesional_id, WaitlistEntry.prestacion_id == prestacion_id, WaitlistEntry.paciente_id == paciente_id, WaitlistEntry.fecha_desde == fecha_desde, WaitlistEntry.fecha_hasta == fecha_hasta, WaitlistEntry.hora_desde == hora_desde, WaitlistEntry.hora_hasta == hora_hasta, WaitlistEntry.estado == "activa").first()


def update(db: Session, item: WaitlistEntry, **values) -> WaitlistEntry:
    for key, value in values.items():
        setattr(item, key, value)
    db.commit(); db.refresh(item)
    return item


def cancel(db: Session, item: WaitlistEntry) -> WaitlistEntry:
    item.estado = "cancelada"; db.commit(); db.refresh(item); return item
