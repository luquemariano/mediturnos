from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.config import settings
from app.integrations.storage import factory
from app.integrations.storage.base import ObjectNotFoundError, ObjectStorageError
from app.integrations.storage.validation import ALLOWED_DOCUMENT_MIME_TYPES, MAX_DOCUMENT_SIZE_BYTES, generate_document_storage_key
from app.models.patient_document import PatientDocument
from app.models.study_request import StudyRequest
from app.repositories.patient_document_repository import buscar_por_id
from app.services.patient_document_service import _filename
from app.services.study_access_token_service import PUBLIC_ERROR, StudyAccessTokenError, verify_study_access_token
from app.services.study_email_service import notify_results_submitted

MAX_ACTIVE_DOCUMENTS = 5

def _error() -> HTTPException: return HTTPException(404, PUBLIC_ERROR, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})
def _request(db: Session, token: str) -> StudyRequest:
    try:
        payload = verify_study_access_token(token=token, secret=settings.study_access_secret.get_secret_value(), ttl_seconds=settings.study_access_token_ttl_seconds)
    except (StudyAccessTokenError, AttributeError): raise _error()
    request = db.query(StudyRequest).filter(StudyRequest.id == payload.study_request_id, StudyRequest.paciente_id == payload.patient_id).first()
    if request is None or request.status != "pending" or (request.expires_at is not None and datetime.now(timezone.utc) >= request.expires_at): raise _error()
    return request

def crear_intent(db: Session, token: str, filename: str, mime_type: str, size_bytes: int):
    request = _request(db, token)
    if mime_type not in ALLOWED_DOCUMENT_MIME_TYPES or size_bytes <= 0 or size_bytes > MAX_DOCUMENT_SIZE_BYTES: raise HTTPException(422, "El archivo no cumple los requisitos permitidos.")
    active = db.query(PatientDocument).filter(PatientDocument.study_request_id == request.id, PatientDocument.origin == "patient", PatientDocument.status.in_(["pending_upload", "available"])).count()
    if active >= MAX_ACTIVE_DOCUMENTS: raise HTTPException(409, "Se alcanzó el máximo de archivos para esta solicitud.")
    document = PatientDocument(paciente_id=request.paciente_id, study_request_id=request.id, origin="patient", uploaded_by_profesional_id=None, storage_key=generate_document_storage_key(mime_type), original_filename=_filename(filename), mime_type=mime_type, size_bytes=size_bytes, category="study_result", status="pending_upload")
    db.add(document)
    try:
        presigned = factory.get_object_storage_provider().create_upload_url(document.storage_key, mime_type, settings.r2_presigned_upload_ttl_seconds)
        db.commit(); db.refresh(document)
    except ObjectStorageError:
        db.rollback(); raise HTTPException(503, "No se pudo preparar la carga.") from None
    return document, presigned

def confirmar(db: Session, token: str, document_id: int):
    request = _request(db, token); document = buscar_por_id(db, document_id)
    if document is None or document.study_request_id != request.id or document.paciente_id != request.paciente_id or document.origin != "patient": raise _error()
    if document.status == "available": return document
    if document.status != "pending_upload": raise HTTPException(409, "El documento no puede confirmarse.")
    try: metadata = factory.get_object_storage_provider().head_object(document.storage_key)
    except (ObjectNotFoundError, ObjectStorageError):
        document.status = "failed"; db.commit(); raise HTTPException(422, "No se pudo verificar el archivo.") from None
    if metadata.size_bytes != document.size_bytes or metadata.content_type != document.mime_type:
        document.status = "failed"; db.commit(); raise HTTPException(422, "La metadata no coincide.")
    document.status = "available"; document.available_at = datetime.now(timezone.utc); db.commit(); db.refresh(document); return document

def remover(db: Session, token: str, document_id: int):
    request = _request(db, token); document = buscar_por_id(db, document_id)
    if document is None or document.study_request_id != request.id or document.paciente_id != request.paciente_id or document.origin != "patient": raise _error()
    if document.status not in {"pending_upload", "available"}: raise HTTPException(409, "El documento no puede eliminarse.")
    document.status = "deleted"; document.deleted_at = datetime.now(timezone.utc); db.commit(); return document

def submit(db: Session, token: str):
    request = _request(db, token)
    documents = db.query(PatientDocument).filter(PatientDocument.study_request_id == request.id, PatientDocument.origin == "patient", PatientDocument.status.in_(["pending_upload", "available"])).all()
    available = [d for d in documents if d.status == "available"]
    if not available or any(d.status == "pending_upload" for d in documents): raise HTTPException(409, "Completá o eliminá los archivos pendientes antes de finalizar.")
    now = datetime.now(timezone.utc); request.status = "submitted"; request.submitted_at = now; request.updated_at = now; db.commit(); notify_results_submitted(request, len(available), now)
    return request, available
