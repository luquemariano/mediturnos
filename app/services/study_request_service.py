from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.study_request import StudyRequest
from app.repositories.paciente_repository import buscar_por_id, buscar_propio
from app.repositories.study_request_repository import buscar_por_id as buscar_solicitud, crear, listar_por_paciente
from app.repositories.turno_repository import buscar_por_id as buscar_turno
from app.schemas.study_request import StudyRequestCreate

def _acceso(db: Session, paciente_id: int, profesional_id: int | None) -> None:
    if profesional_id is None:
        if buscar_por_id(db, paciente_id) is None: raise HTTPException(404, "Paciente no encontrado.")
    elif buscar_propio(db, profesional_id, paciente_id) is None: raise HTTPException(404, "Paciente no encontrado.")
def _owned(db: Session, paciente_id: int, request_id: int, profesional_id: int | None) -> StudyRequest:
    _acceso(db, paciente_id, profesional_id); request = buscar_solicitud(db, request_id)
    if request is None or request.paciente_id != paciente_id: raise HTTPException(404, "Solicitud no encontrada.")
    if profesional_id is not None and request.profesional_id != profesional_id: raise HTTPException(404, "Solicitud no encontrada.")
    return request
def crear_solicitud(db: Session, paciente_id: int, profesional_id: int, datos: StudyRequestCreate) -> StudyRequest:
    _acceso(db, paciente_id, profesional_id); ahora = datetime.now(timezone.utc)
    if datos.expires_at is not None and datos.expires_at <= ahora: raise HTTPException(422, "La fecha de vencimiento debe ser futura.")
    if datos.turno_id is not None:
        turno = buscar_turno(db, datos.turno_id)
        if turno is None or turno.paciente_id != paciente_id or turno.profesional_id != profesional_id: raise HTTPException(422, "El turno no corresponde al paciente y profesional.")
    solicitud = crear(db, paciente_id=paciente_id, profesional_id=profesional_id, turno_id=datos.turno_id, title=datos.title, instructions=datos.instructions, status="pending", requested_at=ahora, expires_at=datos.expires_at, created_at=ahora, updated_at=ahora); db.commit(); db.refresh(solicitud); return solicitud
def listar_solicitudes(db: Session, paciente_id: int, profesional_id: int | None, status: str | None = None):
    _acceso(db, paciente_id, profesional_id)
    if status is not None and status not in {"pending", "submitted", "reviewed", "closed", "cancelled"}: raise HTTPException(422, "Estado inválido.")
    return listar_por_paciente(db, paciente_id, status)
def obtener_solicitud(db: Session, paciente_id: int, request_id: int, profesional_id: int | None): return _owned(db, paciente_id, request_id, profesional_id)
def cancelar_solicitud(db: Session, paciente_id: int, request_id: int, profesional_id: int):
    request = _owned(db, paciente_id, request_id, profesional_id)
    if request.status == "cancelled": return request
    if request.status != "pending": raise HTTPException(409, "La solicitud no puede cancelarse en su estado actual.")
    ahora = datetime.now(timezone.utc); request.status = "cancelled"; request.cancelled_at = ahora; request.updated_at = ahora; db.commit(); db.refresh(request); return request
def cerrar_solicitud(db: Session, paciente_id: int, request_id: int, profesional_id: int):
    request = _owned(db, paciente_id, request_id, profesional_id)
    if request.status == "closed": return request
    if request.status != "pending": raise HTTPException(409, "La solicitud no puede cerrarse en su estado actual.")
    ahora = datetime.now(timezone.utc); request.status = "closed"; request.closed_at = ahora; request.updated_at = ahora; db.commit(); db.refresh(request); return request
