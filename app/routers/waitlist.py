from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.dependencies import obtener_usuario_actual
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.waitlist import WaitlistEntryCreate, WaitlistEntryResponse
from app.services.profesional_service import obtener_mi_profesional
from app.services.waitlist_service import create_waitlist_entry, list_waitlist_entries, cancel_waitlist_entry

router = APIRouter(prefix="/waitlist", tags=["Lista de espera"])


def response(item):
    return {**item.__dict__, "paciente_nombre": f"{item.paciente.nombre} {item.paciente.apellido}", "prestacion_nombre": item.prestacion.nombre}


@router.post("", response_model=WaitlistEntryResponse, status_code=201)
def create(datos: WaitlistEntryCreate, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    profesional = obtener_mi_profesional(db, usuario.id)
    return response(create_waitlist_entry(db, profesional.id, datos))


@router.get("", response_model=list[WaitlistEntryResponse])
def list_items(estado: str | None = Query(None), prestacion_id: int | None = Query(None, gt=0), db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    profesional = obtener_mi_profesional(db, usuario.id)
    return [response(x) for x in list_waitlist_entries(db, profesional.id, estado, prestacion_id)]


@router.post("/{entry_id}/cancel", response_model=WaitlistEntryResponse)
def cancel(entry_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    profesional = obtener_mi_profesional(db, usuario.id)
    return response(cancel_waitlist_entry(db, profesional.id, entry_id))
