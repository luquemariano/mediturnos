import api from "../api/api";
import type { WaitlistEntry } from "../types/waitlist";

export async function listarWaitlist(filtros: { estado?: string; prestacion_id?: number } = {}): Promise<WaitlistEntry[]> {
  return (await api.get<WaitlistEntry[]>("/waitlist", { params: filtros })).data;
}

export async function crearWaitlist(payload: { prestacion_id: number; paciente_id: number; fecha_desde: string; fecha_hasta: string; hora_desde?: string; hora_hasta?: string }): Promise<WaitlistEntry> {
  return (await api.post<WaitlistEntry>("/waitlist", payload)).data;
}

export async function cancelarWaitlist(id: number): Promise<WaitlistEntry> {
  return (await api.post<WaitlistEntry>(`/waitlist/${id}/cancel`)).data;
}
