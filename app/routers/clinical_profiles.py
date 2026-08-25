from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import obtener_usuario_actual
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.clinical_profile import ClinicalProfileResponse, ClinicalProfileUpdate
from app.services.clinical_profile_service import obtener_perfil, upsert_perfil
from app.services.profesional_service import obtener_mi_profesional
router = APIRouter(prefix="/pacientes", tags=["Clinical profile"])
@router.get("/{paciente_id}/clinical-profile", response_model=ClinicalProfileResponse)
def get_clinical_profile(paciente_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    if usuario.rol == "administrador": return obtener_perfil(db, paciente_id, None)
    if usuario.rol != "profesional": raise HTTPException(403, "No tenés permisos para acceder a información clínica.")
    return obtener_perfil(db, paciente_id, obtener_mi_profesional(db, usuario.id).id)
@router.put("/{paciente_id}/clinical-profile", response_model=ClinicalProfileResponse)
def put_clinical_profile(paciente_id: int, datos: ClinicalProfileUpdate, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    if usuario.rol != "profesional": raise HTTPException(403, "Solo un profesional puede editar el resumen clínico.")
    return upsert_perfil(db, paciente_id, obtener_mi_profesional(db, usuario.id).id, datos)
