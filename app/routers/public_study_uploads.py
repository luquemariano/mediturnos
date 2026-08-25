from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.database.connection import obtener_db
from app.schemas.public_study_upload import PublicStudyConfirmRequest, PublicStudyRemoveRequest, PublicStudySubmitRequest, PublicStudySubmitResponse, PublicStudyUploadIntentRequest, PublicStudyUploadIntentResponse
from app.services.public_study_upload_service import confirmar, crear_intent, remover, submit

router = APIRouter(prefix="/public/study-requests", tags=["Public study uploads"])
HEADERS = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}

def _public_error(error: HTTPException) -> HTTPException:
    headers = dict(error.headers or {})
    headers.update(HEADERS)
    return HTTPException(status_code=error.status_code, detail=error.detail, headers=headers)

@router.post("/upload-intents", response_model=PublicStudyUploadIntentResponse)
def upload_intent(datos: PublicStudyUploadIntentRequest, response: Response, db: Session = Depends(obtener_db)):
    response.headers.update(HEADERS)
    try:
        document, presigned = crear_intent(db, datos.token, datos.filename, datos.mime_type, datos.size_bytes)
    except HTTPException as error:
        raise _public_error(error) from None
    return {"document_id": document.id, "upload_url": presigned.url, "expires_in_seconds": presigned.expires_in_seconds, "required_content_type": datos.mime_type}

@router.post("/documents/{document_id}/confirm")
def confirm(document_id: int, datos: PublicStudyConfirmRequest, response: Response, db: Session = Depends(obtener_db)):
    response.headers.update(HEADERS)
    try:
        return confirmar(db, datos.token, document_id)
    except HTTPException as error:
        raise _public_error(error) from None

@router.post("/documents/{document_id}/remove")
def remove(document_id: int, datos: PublicStudyRemoveRequest, response: Response, db: Session = Depends(obtener_db)):
    response.headers.update(HEADERS)
    try:
        return {"status": remover(db, datos.token, document_id).status}
    except HTTPException as error:
        raise _public_error(error) from None

@router.post("/submit", response_model=PublicStudySubmitResponse)
def finalize(datos: PublicStudySubmitRequest, response: Response, db: Session = Depends(obtener_db)):
    response.headers.update(HEADERS)
    try:
        request, documents = submit(db, datos.token)
    except HTTPException as error:
        raise _public_error(error) from None
    return {"status": request.status, "documents": [{"document_id": d.id, "filename": d.original_filename, "size_bytes": d.size_bytes or 0} for d in documents]}
