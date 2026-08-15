import type { EstadoSuscripcion, PlanCode } from "../types/cuenta";
const ESTADOS: Record<EstadoSuscripcion, string> = { trial: "Prueba gratuita", active: "Activo", past_due: "Pago pendiente", cancelled: "Cancelado", expired: "Prueba finalizada" };
const PLANES: Record<PlanCode, string> = { profesional: "Profesional", consultorio: "Consultorio", centro: "Centro" };
export const etiquetaSuscripcion = (estado: EstadoSuscripcion) => ESTADOS[estado];
export const etiquetaPlan = (plan: PlanCode) => PLANES[plan];
export function fechaTrial(fecha: string): string {
  return new Intl.DateTimeFormat("es-AR", { day: "2-digit", month: "2-digit", year: "numeric", timeZone: "America/Argentina/Buenos_Aires" }).format(new Date(fecha));
}
