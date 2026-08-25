import api from "../api/api";
import type { CuentaAdminDetalle, CuentasAdminPagina, CuentasAdminResumen, EventoSuscripcionAdmin, FiltrosCuentasAdmin, PlanAdmin } from "../types/adminCuenta";

export async function obtenerCuentasAdmin(filtros: FiltrosCuentasAdmin, signal?: AbortSignal): Promise<CuentasAdminPagina> {
  return (await api.get<CuentasAdminPagina>("/admin/cuentas", { params: filtros, signal })).data;
}

export async function obtenerResumenCuentasAdmin(): Promise<CuentasAdminResumen> {
  return (await api.get<CuentasAdminResumen>("/admin/cuentas/resumen")).data;
}

export async function obtenerDetalleCuentaAdmin(cuentaId: number, signal?: AbortSignal): Promise<CuentaAdminDetalle> {
  return (await api.get<CuentaAdminDetalle>(`/admin/cuentas/${cuentaId}`, { signal })).data;
}

export async function obtenerHistorialCuentaAdmin(cuentaId: number): Promise<EventoSuscripcionAdmin[]> { return (await api.get(`/admin/cuentas/${cuentaId}/suscripcion/historial`)).data; }
const postAccion = async (cuentaId: number, accion: string, data: object): Promise<CuentaAdminDetalle> => (await api.post(`/admin/cuentas/${cuentaId}/suscripcion/${accion}`, data)).data;
export const activarSuscripcionAdmin = (id: number, motivo: string) => postAccion(id, "activar", { motivo });
export const reactivarSuscripcionAdmin = (id: number, motivo: string) => postAccion(id, "reactivar", { motivo });
export const marcarPagoPendienteAdmin = (id: number, motivo: string) => postAccion(id, "marcar-pago-pendiente", { motivo });
export const cancelarSuscripcionAdmin = (id: number, motivo: string) => postAccion(id, "cancelar", { motivo });
export const extenderTrialAdmin = (id: number, dias: 7 | 14 | 30, motivo: string) => postAccion(id, "extender-trial", { dias, motivo });
export const cambiarPlanAdmin = (id: number, plan: PlanAdmin, motivo: string) => postAccion(id, "cambiar-plan", { plan, motivo });
