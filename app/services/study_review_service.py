from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.models.evolucion_clinica import EvolucionClinica
from app.models.study_request import StudyRequest
from app.models.study_review import StudyReview
from app.repositories.patient_document_repository import listar_disponibles_por_solicitud
from app.repositories.paciente_repository import buscar_propio
from app.schemas.study_review import StudyReviewCreate
from app.services.study_email_service import notify_review_created

DISPOSITION_LABELS = {"online_response": "respuesta online", "requires_in_person": "requiere consulta presencial", "requires_teleconsultation": "requiere teleconsulta"}

def _request(db, paciente_id, request_id, profesional_id):
    if buscar_propio(db, profesional_id, paciente_id) is None:
        raise HTTPException(404, "Paciente no encontrado.")
    request = db.query(StudyRequest).options(joinedload(StudyRequest.review), joinedload(StudyRequest.profesional)).filter(StudyRequest.id == request_id, StudyRequest.paciente_id == paciente_id, StudyRequest.profesional_id == profesional_id).first()
    if request is None: raise HTTPException(404, "Solicitud de estudio no encontrada.")
    return request

def obtener_review(db: Session, paciente_id: int, request_id: int, profesional_id: int):
    request = _request(db, paciente_id, request_id, profesional_id)
    if request.review is None: raise HTTPException(404, "La devolución todavía no existe.")
    return request.review

def crear_review(db: Session, paciente_id: int, request_id: int, profesional_id: int, datos: StudyReviewCreate):
    request = _request(db, paciente_id, request_id, profesional_id)
    if request.status != "submitted": raise HTTPException(409, "La solicitud no está lista para revisión.")
    if not listar_disponibles_por_solicitud(db, paciente_id, request_id): raise HTTPException(409, "La solicitud no tiene documentos disponibles para revisar.")
    try:
        review = StudyReview(study_request_id=request.id, profesional_id=profesional_id, review_text=datos.review_text, disposition=datos.disposition)
        db.add(review); db.flush()
        request.status = "reviewed"; request.reviewed_at = datetime.now(timezone.utc); request.updated_at = datetime.now(timezone.utc)
        db.add(EvolucionClinica(paciente_id=paciente_id, profesional_id=profesional_id, contenido=f"Devolución de estudio: {request.title}. Resolución: {DISPOSITION_LABELS[datos.disposition]}.", tipo="study_review", study_review_id=review.id))
        db.commit(); db.refresh(review)
    except IntegrityError:
        db.rollback(); raise HTTPException(409, "La solicitud ya tiene una devolución registrada.") from None
    notify_review_created(review)
    return review
