import type { EstadoSuscripcion, PlanCode } from "./cuenta";

export interface InicioSuscripcionRespuesta {
  estado: EstadoSuscripcion;
  checkout_url: string | null;
}

export interface EstadoSuscripcionSaas {
  cuenta_id: number;
  plan: PlanCode;
  estado: EstadoSuscripcion;
  trial_started_at: string | null;
  trial_ends_at: string | null;
  billing_provider: "manual" | "mercadopago";
  provider_status: string | null;
  next_payment_at: string | null;
  cancelled_at: string | null;
}
