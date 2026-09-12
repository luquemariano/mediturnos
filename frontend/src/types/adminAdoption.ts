export type AdoptionStatus = "sin_uso" | "configurando" | "activo" | "en_riesgo" | "inactivo";

export interface AdminAdoptionItem {
  usuario_id: number;
  profesional_id: number;
  cuenta_id: number;
  nombre: string;
  apellido: string;
  email: string;
  first_login_at: string | null;
  last_login_at: string | null;
  login_count: number;
  last_activity_at: string | null;
  days_since_last_activity: number | null;
  active_days: number;
  patients_created: number;
  appointments_created: number;
  services_created: number;
  availabilities_created: number;
  clinical_evolutions_created: number;
  adoption_status: AdoptionStatus;
}

export interface FiltrosAdopcionAdmin { status?: AdoptionStatus; q?: string; }
