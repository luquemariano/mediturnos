from datetime import datetime, timedelta, timezone
import hashlib, secrets, logging
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.datetime_utils import ahora_negocio, desde_base_utc, utc_a_zona_negocio
from app.core.public_booking import generar_token_autogestion, hash_token_autogestion
from app.models.waitlist_entry import WaitlistEntry
from app.models.waitlist_offer import WaitlistOffer
from app.repositories import waitlist_offer_repository as repo
from app.services.waitlist_service import ReleasedSlot
from app.services.disponibilidad_service import obtener_horarios_libres
from app.services.turno_service import crear_turno
from app.schemas.turno import TurnoCrear
from app.services.email_service import enviar_confirmacion_reserva_publica
logger = logging.getLogger("mediturnos.waitlist_offer")

def _normalizar_timestamps(offer):
    offer.expires_at = desde_base_utc(offer.expires_at)
    offer.created_at = desde_base_utc(offer.created_at)
    return offer

def _validar_slot(db, offer):
    now = ahora_negocio(); inicio = utc_a_zona_negocio(desde_base_utc(offer.slot_inicio))
    if desde_base_utc(offer.expires_at) <= now.astimezone(timezone.utc) or inicio <= now + timedelta(hours=2): return False
    return any(desde_base_utc(x["fecha_hora"]) == desde_base_utc(offer.slot_inicio) for x in obtener_horarios_libres(db, offer.prestacion_id, inicio.date(), fecha_actual=now.date()))

def _cargar(db, token):
    if not token or len(token) > 512: raise HTTPException(404, "Oferta no encontrada.")
    offer = repo.get_by_token_hash(db, hash_token_autogestion(token))
    if offer is None: raise HTTPException(404, "Oferta no encontrada.")
    if offer.estado == "activa" and datetime.now(timezone.utc) >= desde_base_utc(offer.expires_at):
        offer.estado = "vencida"
        if offer.entry.estado == "ofertada": offer.entry.estado = "activa"
        db.commit(); db.refresh(offer)
        _normalizar_timestamps(offer)
        logger.info("waitlist_offer_expired offer_id=%s waitlist_entry_id=%s", offer.id, offer.waitlist_entry_id)
    return _normalizar_timestamps(offer)

def create_waitlist_offer(db: Session, entry: WaitlistEntry, slot: ReleasedSlot):
    if entry.estado != "activa": raise HTTPException(409, "La entrada no está activa.")
    if repo.get_active_for_entry(db, entry.id) or repo.get_active_for_slot(db, slot.profesional_id, slot.prestacion_id, slot.fecha_hora): raise HTTPException(409, "Ya existe una oferta activa.")
    if not any(desde_base_utc(x["fecha_hora"]) == desde_base_utc(slot.fecha_hora) for x in obtener_horarios_libres(db, slot.prestacion_id, utc_a_zona_negocio(slot.fecha_hora).date(), fecha_actual=ahora_negocio().date())): raise HTTPException(409, "El horario ya no está disponible.")
    token = secrets.token_urlsafe(32); now = datetime.now(timezone.utc)
    offer = repo.create(db, waitlist_entry_id=entry.id, profesional_id=slot.profesional_id, prestacion_id=slot.prestacion_id, slot_inicio=slot.fecha_hora, slot_fin=slot.fecha_fin, token_hash=hash_token_autogestion(token), expires_at=now + timedelta(minutes=30))
    entry.estado = "ofertada"; db.commit(); db.refresh(offer); _normalizar_timestamps(offer)
    logger.info("waitlist_offer_created offer_id=%s waitlist_entry_id=%s profesional_id=%s prestacion_id=%s", offer.id, entry.id, slot.profesional_id, slot.prestacion_id)
    return offer, token

def offer_public_view(db, token):
    offer = _cargar(db, token)
    return offer

def accept_waitlist_offer(db: Session, token: str):
    offer = _cargar(db, token)
    if offer.estado == "aceptada": return offer, None
    if offer.estado != "activa" or offer.entry.estado != "ofertada": raise HTTPException(409, "La oferta ya no está disponible.")
    if not _validar_slot(db, offer):
        offer.estado = "vencida"; offer.entry.estado = "activa"; db.commit(); logger.info("waitlist_offer_slot_unavailable offer_id=%s", offer.id); raise HTTPException(409, "El horario ya no está disponible.")
    turno = crear_turno(db, TurnoCrear(paciente_id=offer.entry.paciente_id, prestacion_id=offer.prestacion_id, fecha_hora=desde_base_utc(offer.slot_inicio)), ahora_referencia=datetime.now(timezone.utc))
    autogestion_token = generar_token_autogestion()
    turno.autogestion_token_hash = hash_token_autogestion(autogestion_token)
    offer.estado = "aceptada"; offer.accepted_at = datetime.now(timezone.utc); offer.entry.estado = "reservada"; db.commit(); db.refresh(offer); _normalizar_timestamps(offer)
    logger.info("waitlist_offer_accepted offer_id=%s waitlist_entry_id=%s", offer.id, offer.waitlist_entry_id)
    try:
        enviar_confirmacion_reserva_publica(
            destinatario=offer.entry.paciente.email,
            paciente=f"{offer.entry.paciente.nombre} {offer.entry.paciente.apellido}",
            profesional=f"{offer.entry.profesional.nombre} {offer.entry.profesional.apellido}",
            prestacion=offer.entry.prestacion.nombre,
            modalidad=offer.entry.prestacion.modalidad,
            fecha_hora=desde_base_utc(turno.fecha_hora),
            autogestion_token=autogestion_token,
        )
    except Exception:
        logger.warning("waitlist_offer_confirmation_email_failed offer_id=%s turn_id=%s", offer.id, turno.id)
    return offer, turno
