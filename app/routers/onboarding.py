from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import obtener_usuario_actual
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.onboarding import OnboardingAvance, OnboardingRespuesta
from app.services.onboarding_service import avanzar_onboarding, completar_onboarding, obtener_estado_onboarding
from app.services.profesional_service import obtener_mi_profesional

router = APIRouter(prefix="/onboarding", tags=["Onboarding profesional"])


def profesional_actual(db: Session, usuario: Usuario):
    if usuario.rol != "profesional":
        raise HTTPException(status_code=403, detail="El usuario autenticado no es un profesional.")
    return obtener_mi_profesional(db, usuario.id)


@router.get("/me", response_model=OnboardingRespuesta)
def ver_onboarding(db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return obtener_estado_onboarding(db, profesional_actual(db, usuario))


@router.patch("/me", response_model=OnboardingRespuesta)
def avanzar(datos: OnboardingAvance, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return avanzar_onboarding(db, profesional_actual(db, usuario), datos.siguiente_paso)


@router.post("/me/completar", response_model=OnboardingRespuesta)
def completar(db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return completar_onboarding(db, profesional_actual(db, usuario))
