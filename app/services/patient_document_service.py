from datetime import datetime, timezone
import re
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.integrations.storage import factory
from app.integrations.storage.base import ObjectNotFoundError, ObjectStorageError
from app.integrations.storage.validation import ALLOWED_DOCUMENT_MIME_TYPES, MAX_DOCUMENT_SIZE_BYTES, generate_document_storage_key
from app.models.patient_document import PatientDocument
from app.repositories.patient_document_repository import buscar_por_id, crear_pending, listar_disponibles
from app.repositories.paciente_repository import buscar_por_id as buscar_paciente, buscar_propio
from app.schemas.patient_document import PatientDocumentUploadIntentRequest
from app.core.config import settings

CATEGORIES = {"laboratory", "imaging", "order", "report", "prescription", "other", "study_result"}

def _acceso(db: Session, paciente_id: int, profesional_id: int | None) -> None:
    if profesional_id is None:
        if buscar_paciente(db, paciente_id) is None: raise HTTPException(404, "Paciente no encontrado.")
    elif buscar_propio(db, profesional_id, paciente_id) is None:
        raise HTTPException(404, "Paciente no encontrado.")

def _documento_propio(db: Session, paciente_id: int, document_id: int) -> PatientDocument:
    documento = buscar_por_id(db, document_id)
    if documento is None or documento.paciente_id != paciente_id: raise HTTPException(404, "Documento no encontrado.")
    return documento

def _filename(filename: str) -> str:
    limpio = filename.replace("\\", "/").split("/")[-1].strip()
    limpio = re.sub(r"[^\w. ()\-áéíóúÁÉÍÓÚñÑ]", "_", limpio)
    return (limpio or "documento")[:255]

def _provider(): return factory.get_object_storage_provider()

def crear_intent(db: Session, paciente_id: int, profesional_id: int, datos: PatientDocumentUploadIntentRequest):
    _acceso(db, paciente_id, profesional_id)
    if datos.mime_type not in ALLOWED_DOCUMENT_MIME_TYPES: raise HTTPException(422, "Tipo de archivo no permitido.")
    if datos.size_bytes <= 0 or datos.size_bytes > MAX_DOCUMENT_SIZE_BYTES: raise HTTPException(422, "El tamaño del archivo no es válido.")
    documento = crear_pending(db, paciente_id=paciente_id, uploaded_by_profesional_id=profesional_id, storage_key=generate_document_storage_key(datos.mime_type), original_filename=_filename(datos.filename), mime_type=datos.mime_type, size_bytes=datos.size_bytes, category=datos.category)
    try:
        presigned = _provider().create_upload_url(documento.storage_key, datos.mime_type, settings.r2_presigned_upload_ttl_seconds)
        db.commit(); db.refresh(documento)
    except ObjectStorageError:
        db.rollback(); raise HTTPException(503, "No se pudo preparar la carga del documento.") from None
    return documento, presigned

def confirmar(db: Session, paciente_id: int, profesional_id: int, document_id: int):
    _acceso(db, paciente_id, profesional_id); documento = _documento_propio(db, paciente_id, document_id)
    if documento.status == "available": return documento
    if documento.status != "pending_upload": raise HTTPException(409, "El documento no puede confirmarse en su estado actual.")
    try: metadata = _provider().head_object(documento.storage_key)
    except (ObjectNotFoundError, ObjectStorageError):
        documento.status = "failed"; db.commit(); raise HTTPException(422, "No se pudo verificar el documento cargado.") from None
    if metadata.size_bytes != documento.size_bytes or metadata.content_type != documento.mime_type:
        documento.status = "failed"; db.commit(); raise HTTPException(422, "La metadata del documento no coincide.")
    documento.status = "available"; documento.available_at = datetime.now(timezone.utc); db.commit(); db.refresh(documento); return documento

def listar(db: Session, paciente_id: int, profesional_id: int | None):
    _acceso(db, paciente_id, profesional_id); return listar_disponibles(db, paciente_id)

def download_url(db: Session, paciente_id: int, document_id: int, profesional_id: int | None):
    _acceso(db, paciente_id, profesional_id); documento = _documento_propio(db, paciente_id, document_id)
    if documento.status != "available": raise HTTPException(409, "El documento no está disponible.")
    try: return _provider().create_download_url(documento.storage_key, settings.r2_presigned_download_ttl_seconds)
    except ObjectStorageError: raise HTTPException(503, "No se pudo preparar la descarga.") from None

def eliminar(db: Session, paciente_id: int, profesional_id: int, document_id: int):
    _acceso(db, paciente_id, profesional_id); documento = _documento_propio(db, paciente_id, document_id)
    if documento.status == "deleted": raise HTTPException(409, "El documento ya fue eliminado.")
    if documento.status != "available": raise HTTPException(409, "El documento no puede eliminarse en su estado actual.")
    documento.status = "deleted"; documento.deleted_at = datetime.now(timezone.utc); documento.deleted_by_profesional_id = profesional_id; db.commit(); db.refresh(documento); return documento
