export type EstadoSuscripcion = "trial" | "active" | "past_due" | "cancelled" | "expired";
export type PlanCode = "profesional" | "consultorio" | "centro";
export interface CuentaActual { cuenta_id: number; plan: PlanCode; subscription_status: EstadoSuscripcion; trial_started_at: string | null; trial_ends_at: string | null; trial_days_remaining: number; }
