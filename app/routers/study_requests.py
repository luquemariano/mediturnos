from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.dependencies import obtener_usuario_actual
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.study_request import StudyRequestCreate, StudyRequestResponse
from app.services.profesional_service import obtener_mi_profesional
from app.services.study_request_service import cancelar_solicitud, cerrar_solicitud, crear_solicitud, listar_solicitudes, obtener_solicitud
router = APIRouter(prefix="/pacientes", tags=["Study requests"])
def _prof(usuario: Usuario, db: Session) -> int:
    if usuario.rol != "profesional": raise HTTPException(403, "No tenés permisos para gestionar solicitudes de estudios.")
    return obtener_mi_profesional(db, usuario.id).id
def _read_role(usuario: Usuario, db: Session) -> int | None:
    if usuario.rol == "administrador": return None
    return _prof(usuario, db)
@router.post("/{paciente_id}/study-requests", response_model=StudyRequestResponse, status_code=201)
def create_request(paciente_id: int, datos: StudyRequestCreate, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return crear_solicitud(db, paciente_id, _prof(usuario, db), datos)
@router.get("/{paciente_id}/study-requests", response_model=list[StudyRequestResponse])
def list_requests(paciente_id: int, status: str | None = Query(default=None), db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return listar_solicitudes(db, paciente_id, _read_role(usuario, db), status)
@router.get("/{paciente_id}/study-requests/{request_id}", response_model=StudyRequestResponse)
def get_request(paciente_id: int, request_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return obtener_solicitud(db, paciente_id, request_id, _read_role(usuario, db))
@router.post("/{paciente_id}/study-requests/{request_id}/cancel", response_model=StudyRequestResponse)
def cancel_request(paciente_id: int, request_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return cancelar_solicitud(db, paciente_id, request_id, _prof(usuario, db))
@router.post("/{paciente_id}/study-requests/{request_id}/close", response_model=StudyRequestResponse)
def close_request(paciente_id: int, request_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return cerrar_solicitud(db, paciente_id, request_id, _prof(usuario, db))
