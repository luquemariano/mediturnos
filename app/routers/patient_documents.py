from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import obtener_usuario_actual
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.patient_document import PatientDocumentDownloadUrlResponse, PatientDocumentResponse, PatientDocumentUploadIntentRequest, PatientDocumentUploadIntentResponse
from app.services.patient_document_service import confirmar, crear_intent, download_url, eliminar, listar, listar_por_solicitud
from app.services.profesional_service import obtener_mi_profesional
router = APIRouter(prefix="/pacientes", tags=["Patient documents"])
def _profesional(usuario: Usuario, db: Session):
    if usuario.rol != "profesional": raise HTTPException(403, "No tenés permisos para acceder a documentos clínicos.")
    return obtener_mi_profesional(db, usuario.id).id
@router.post("/{paciente_id}/documents/upload-intents", response_model=PatientDocumentUploadIntentResponse, status_code=201)
def upload_intent(paciente_id: int, datos: PatientDocumentUploadIntentRequest, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    documento, presigned = crear_intent(db, paciente_id, _profesional(usuario, db), datos)
    return {"document_id": documento.id, "upload_url": presigned.url, "expires_in_seconds": presigned.expires_in_seconds, "required_content_type": datos.mime_type}
@router.post("/{paciente_id}/documents/{document_id}/confirm", response_model=PatientDocumentResponse)
def confirm(paciente_id: int, document_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return confirmar(db, paciente_id, _profesional(usuario, db), document_id)
@router.get("/{paciente_id}/documents", response_model=list[PatientDocumentResponse])
def list_documents(paciente_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    profesional_id = None if usuario.rol == "administrador" else _profesional(usuario, db)
    return listar(db, paciente_id, profesional_id)
@router.get("/{paciente_id}/study-requests/{request_id}/documents", response_model=list[PatientDocumentResponse])
def list_request_documents(paciente_id: int, request_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    profesional_id = None if usuario.rol == "administrador" else _profesional(usuario, db)
    return listar_por_solicitud(db, paciente_id, request_id, profesional_id)
@router.post("/{paciente_id}/documents/{document_id}/download-url", response_model=PatientDocumentDownloadUrlResponse)
def get_download_url(paciente_id: int, document_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    profesional_id = None if usuario.rol == "administrador" else _profesional(usuario, db)
    url = download_url(db, paciente_id, document_id, profesional_id)
    return {"download_url": url.url, "expires_in_seconds": url.expires_in_seconds}
@router.delete("/{paciente_id}/documents/{document_id}", response_model=PatientDocumentResponse)
def delete_document(paciente_id: int, document_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return eliminar(db, paciente_id, _profesional(usuario, db), document_id)
