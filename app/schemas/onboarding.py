from pydantic import BaseModel, ConfigDict

from app.schemas.profesional import OnboardingStep, ProfesionalRespuesta


class OnboardingAvance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    siguiente_paso: OnboardingStep


class OnboardingRespuesta(BaseModel):
    onboarding_step: OnboardingStep
    perfil: ProfesionalRespuesta
    tiene_prestaciones: bool
    tiene_disponibilidad: bool
