from dataclasses import dataclass
from datetime import date, datetime, timezone, timedelta
import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.repositories import waitlist_repository as repo
from app.schemas.waitlist import WaitlistEntryCreate
from app.services.paciente_service import paciente_pertenece_a_profesional
from app.core.datetime_utils import fecha_actual_negocio
from app.core.datetime_utils import ahora_negocio, utc_a_zona_negocio, desde_base_utc
from app.services.disponibilidad_service import obtener_horarios_libres

logger = logging.getLogger("turnelia.waitlist")


@dataclass(frozen=True)
class ReleasedSlot:
    profesional_id: int
    prestacion_id: int
    fecha_hora: datetime
    fecha_fin: datetime


def find_matching_waitlist_entries(db: Session, slot: ReleasedSlot):
    """Return active, currently compatible entries without changing their state."""
    inicio = utc_a_zona_negocio(desde_base_utc(slot.fecha_hora))
    fin = utc_a_zona_negocio(desde_base_utc(slot.fecha_fin))
    ahora = ahora_negocio()
    logger.info("waitlist_match_check profesional_id=%s prestacion_id=%s slot=%s", slot.profesional_id, slot.prestacion_id, desde_base_utc(slot.fecha_hora).isoformat())
    if inicio <= ahora + timedelta(hours=2) or inicio > ahora + timedelta(days=60):
        logger.info("waitlist_match_none profesional_id=%s prestacion_id=%s count=0", slot.profesional_id, slot.prestacion_id)
        return []
    candidatos = repo.list_active_candidates(db, slot.profesional_id, slot.prestacion_id, inicio.date())
    libres = obtener_horarios_libres(db, slot.prestacion_id, inicio.date(), fecha_actual=ahora.date())
    inicio_utc = desde_base_utc(slot.fecha_hora)
    duracion = (fin - inicio).total_seconds()
    resultado = []
    for item in candidatos:
        if item.hora_desde is not None and not (item.hora_desde <= inicio.time() and inicio.time() < item.hora_hasta):
            continue
        prestacion = item.prestacion
        if duracion < prestacion.duracion_minutos * 60:
            continue
        if any(desde_base_utc(x["fecha_hora"]) == inicio_utc for x in libres):
            resultado.append(item)
    logger.info("waitlist_match_%s profesional_id=%s prestacion_id=%s count=%s", "found" if resultado else "none", slot.profesional_id, slot.prestacion_id, len(resultado))
    return resultado


def create_waitlist_entry(db: Session, profesional_id: int, datos: WaitlistEntryCreate, *, origen: str = "profesional"):
    profesional = db.get(Profesional, profesional_id)
    prestacion = db.get(Prestacion, datos.prestacion_id)
    paciente = db.get(Paciente, datos.paciente_id)
    if profesional is None or not profesional.activo:
        raise HTTPException(404, "Profesional no encontrado.")
    if prestacion is None or prestacion.profesional_id != profesional_id:
        raise HTTPException(404, "Prestación no encontrada.")
    if not prestacion.activa:
        raise HTTPException(409, "La prestación está inactiva.")
    if paciente is None or not paciente.activo or not paciente_pertenece_a_profesional(db, profesional_id, datos.paciente_id):
        raise HTTPException(404, "Paciente no encontrado.")
    if datos.fecha_desde < fecha_actual_negocio():
        raise HTTPException(400, "La fecha desde no puede ser anterior a hoy.")
    if repo.get_active_duplicate(db, profesional_id, datos.prestacion_id, datos.paciente_id, datos.fecha_desde, datos.fecha_hasta, datos.hora_desde, datos.hora_hasta):
        raise HTTPException(409, "Ya existe una entrada activa equivalente.")
    item = repo.create(db, profesional_id=profesional_id, prestacion_id=datos.prestacion_id, paciente_id=datos.paciente_id, fecha_desde=datos.fecha_desde, fecha_hasta=datos.fecha_hasta, hora_desde=datos.hora_desde, hora_hasta=datos.hora_hasta, origen=origen)
    db.commit(); db.refresh(item)
    return item


def list_waitlist_entries(db: Session, profesional_id: int, estado: str | None = None, prestacion_id: int | None = None):
    if estado and estado not in {"activa", "ofertada", "reservada", "cancelada", "vencida"}:
        raise HTTPException(400, "Estado de lista de espera inválido.")
    return repo.list_by_profesional(db, profesional_id, estado, prestacion_id)


def cancel_waitlist_entry(db: Session, profesional_id: int, entry_id: int):
    item = repo.get_by_id(db, entry_id, profesional_id)
    if item is None:
        raise HTTPException(404, "Entrada de lista de espera no encontrada.")
    if item.estado == "cancelada":
        return item
    if item.estado != "activa":
        raise HTTPException(409, "La entrada no puede cancelarse en su estado actual.")
    return repo.cancel(db, item)
