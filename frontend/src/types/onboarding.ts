import type { OnboardingStep } from "./auth";
import type { Profesional } from "./profesional";

export interface OnboardingEstado { onboarding_step: OnboardingStep; perfil: Profesional; tiene_prestaciones: boolean; tiene_disponibilidad: boolean; }
