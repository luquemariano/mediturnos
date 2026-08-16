export type PlanAdmin = "profesional" | "consultorio" | "centro";
export type EstadoAdmin = "trial" | "active" | "past_due" | "cancelled" | "expired" | "sin_suscripcion";

export interface ProfesionalPrincipalAdmin { profesional_id: number; nombre: string; apellido: string; matricula: string; email: string | null; }
export interface CuentaAdminItem { cuenta_id: number; nombre: string; tipo: "individual" | "organizacion"; plan: PlanAdmin | null; estado: EstadoAdmin; created_at: string; trial_ends_at: string | null; profesionales_count: number; miembros_count: number; profesional_principal: ProfesionalPrincipalAdmin | null; }
export interface CuentasAdminPagina { items: CuentaAdminItem[]; total: number; offset: number; limit: number; }
export interface CuentasAdminResumen { cuentas_totales: number; trials_activos: number; suscripciones_activas: number; trials_finalizados: number; altas_ultimos_30_dias: number; }
export interface CuentaAdminDetalle {
  cuenta: { id: number; nombre: string; tipo: "individual" | "organizacion"; created_at: string; updated_at: string };
  suscripcion: null | { plan: PlanAdmin; estado: Exclude<EstadoAdmin, "sin_suscripcion">; estado_persistido: Exclude<EstadoAdmin, "sin_suscripcion"> | null; trial_started_at: string | null; trial_ends_at: string | null; trial_days_remaining: number };
  miembros: Array<{ usuario_id: number; nombre: string; email: string; rol_cuenta: "propietario" | "administrador" | "miembro"; activo: boolean; miembro_desde: string }>;
  profesionales: Array<{ id: number; nombre: string; apellido: string; matricula: string; email: string | null; activo: boolean }>;
}

export interface FiltrosCuentasAdmin { q?: string; estado?: string; plan?: string; created_from?: string; offset: number; limit: number; }
export interface EventoSuscripcionAdmin { id: number; actor_usuario_id: number | null; actor_nombre: string | null; actor_tipo: "usuario" | "sistema"; accion: string; estado_anterior: Exclude<EstadoAdmin, "sin_suscripcion"> | null; estado_nuevo: Exclude<EstadoAdmin, "sin_suscripcion"> | null; plan_anterior: PlanAdmin | null; plan_nuevo: PlanAdmin | null; motivo: string | null; created_at: string; }
