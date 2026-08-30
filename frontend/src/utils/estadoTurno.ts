import type { EstadoTurno } from "../types/turno";

export function etiquetaEstado(estado: EstadoTurno): string {
  return estado === "reservado" ? "Pendiente" : estado.charAt(0).toUpperCase() + estado.slice(1);
}
