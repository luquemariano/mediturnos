from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.disponibilidad import Disponibilidad
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.schemas.onboarding import OnboardingRespuesta

PASOS = ("perfil", "prestaciones", "disponibilidad", "listo", "completado")


def obtener_estado_onboarding(db: Session, profesional: Profesional) -> OnboardingRespuesta:
    tiene_prestaciones = db.query(Prestacion.id).filter(
        Prestacion.profesional_id == profesional.id, Prestacion.activa.is_(True),
    ).first() is not None
    tiene_disponibilidad = db.query(Disponibilidad.id).filter(
        Disponibilidad.profesional_id == profesional.id, Disponibilidad.activa.is_(True),
    ).first() is not None
    return OnboardingRespuesta(
        onboarding_step=profesional.onboarding_step,
        perfil=profesional,
        tiene_prestaciones=tiene_prestaciones,
        tiene_disponibilidad=tiene_disponibilidad,
    )


def avanzar_onboarding(db: Session, profesional: Profesional, siguiente_paso: str):
    actual = PASOS.index(profesional.onboarding_step)
    destino = PASOS.index(siguiente_paso)
    if siguiente_paso == "completado":
        raise HTTPException(status_code=400, detail="Usá la acción de completar onboarding.")
    if destino > actual + 1:
        raise HTTPException(status_code=400, detail="La transición de onboarding no es válida.")
    if destino > actual:
        profesional.onboarding_step = siguiente_paso
        db.commit()
        db.refresh(profesional)
    return obtener_estado_onboarding(db, profesional)


def completar_onboarding(db: Session, profesional: Profesional):
    if profesional.onboarding_step != "completado":
        if PASOS.index(profesional.onboarding_step) < PASOS.index("listo"):
            raise HTTPException(status_code=400, detail="Completá los pasos anteriores antes de finalizar.")
        profesional.onboarding_step = "completado"
        db.commit()
        db.refresh(profesional)
    return obtener_estado_onboarding(db, profesional)
