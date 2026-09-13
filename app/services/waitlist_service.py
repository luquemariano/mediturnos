from datetime import date, datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.repositories import waitlist_repository as repo
from app.schemas.waitlist import WaitlistEntryCreate
from app.services.paciente_service import paciente_pertenece_a_profesional
from app.core.datetime_utils import fecha_actual_negocio


def create_waitlist_entry(db: Session, profesional_id: int, datos: WaitlistEntryCreate):
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
    item = repo.create(db, profesional_id=profesional_id, prestacion_id=datos.prestacion_id, paciente_id=datos.paciente_id, fecha_desde=datos.fecha_desde, fecha_hasta=datos.fecha_hasta, hora_desde=datos.hora_desde, hora_hasta=datos.hora_hasta, origen="profesional")
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
