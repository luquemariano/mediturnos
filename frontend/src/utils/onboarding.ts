import type { OnboardingStep } from "../types/auth";

const RUTAS: Record<OnboardingStep, string> = {
  perfil: "/onboarding/perfil",
  prestaciones: "/onboarding/prestaciones",
  disponibilidad: "/onboarding/disponibilidad",
  listo: "/onboarding/listo",
  completado: "/app",
};

export function rutaOnboarding(paso: OnboardingStep) { return RUTAS[paso]; }
