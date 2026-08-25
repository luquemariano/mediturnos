import api from "../api/api";
import type { OnboardingStep } from "../types/auth";
import type { OnboardingEstado } from "../types/onboarding";

export async function obtenerOnboarding(): Promise<OnboardingEstado> { return (await api.get<OnboardingEstado>("/onboarding/me")).data; }
export async function avanzarOnboarding(siguiente_paso: OnboardingStep): Promise<OnboardingEstado> { return (await api.patch<OnboardingEstado>("/onboarding/me", { siguiente_paso })).data; }
export async function completarOnboarding(): Promise<OnboardingEstado> { return (await api.post<OnboardingEstado>("/onboarding/me/completar")).data; }
