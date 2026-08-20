from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from app.core.dependencies import obtener_usuario_actual
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.models.study_request import StudyRequest
from app.schemas.study_request import StudyRequestCreate, StudyRequestResponse
from app.services.profesional_service import obtener_mi_profesional
from app.services.study_request_service import cancelar_solicitud, cerrar_solicitud, crear_solicitud, listar_solicitudes, obtener_solicitud
from app.services.study_request_service import obtener_solicitud_para_access
from app.schemas.study_access import StudyAccessLinkResponse, PublicStudyRequestResponse
from app.services.study_access_token_service import PUBLIC_ERROR, StudyAccessTokenError, create_study_access_token, verify_study_access_token
from app.core.config import settings
from app.schemas.study_review import StudyReviewCreate, StudyReviewResponse
from app.services.study_review_service import crear_review, obtener_review
router = APIRouter(prefix="/pacientes", tags=["Study requests"])
public_router = APIRouter(prefix="/public/study-requests", tags=["Public study requests"])
PUBLIC_HEADERS = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}
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
@router.get("/{paciente_id}/study-requests/{request_id}/review", response_model=StudyReviewResponse)
def get_review(paciente_id: int, request_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return obtener_review(db, paciente_id, request_id, _prof(usuario, db))
@router.post("/{paciente_id}/study-requests/{request_id}/review", response_model=StudyReviewResponse, status_code=201)
def post_review(paciente_id: int, request_id: int, datos: StudyReviewCreate, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return crear_review(db, paciente_id, request_id, _prof(usuario, db), datos)

@router.post("/{paciente_id}/study-requests/{request_id}/access-link", response_model=StudyAccessLinkResponse)
def create_access_link(paciente_id: int, request_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    request = obtener_solicitud_para_access(db, paciente_id, request_id, _prof(usuario, db))
    if not settings.study_access_secret:
        raise HTTPException(500, "La configuración de acceso de estudios no está disponible.")
    token = create_study_access_token(secret=settings.study_access_secret.get_secret_value(), study_request_id=request.id, patient_id=request.paciente_id)
    expires = settings.study_access_token_ttl_seconds
    if request.expires_at is not None:
        expires = max(0, min(expires, int((request.expires_at - datetime.now(UTC)).total_seconds())))
    return {"url": f"{settings.frontend_url}/estudios/enviar?token={token}", "expires_in_seconds": expires}

@public_router.get("/access", response_model=PublicStudyRequestResponse)
def public_access(token: str = Query(min_length=1), response: Response = None, db: Session = Depends(obtener_db)):
    if response is not None:
        response.headers.update(PUBLIC_HEADERS)
    try:
        if not settings.study_access_secret:
            raise StudyAccessTokenError(PUBLIC_ERROR)
        payload = verify_study_access_token(token=token, secret=settings.study_access_secret.get_secret_value(), ttl_seconds=settings.study_access_token_ttl_seconds)
        request = db.query(StudyRequest).filter(StudyRequest.id == payload.study_request_id, StudyRequest.paciente_id == payload.patient_id).first()
        if request is None or request.status != "pending" or (request.expires_at is not None and datetime.now(UTC) >= request.expires_at):
            raise StudyAccessTokenError(PUBLIC_ERROR)
        professional = request.profesional
        return {"study_request_id": request.id, "professional_name": f"{professional.nombre} {professional.apellido}".strip(), "title": request.title, "instructions": request.instructions, "requested_at": request.requested_at, "expires_at": request.expires_at, "status": request.status}
    except StudyAccessTokenError:
        raise HTTPException(404, PUBLIC_ERROR, headers=PUBLIC_HEADERS)
