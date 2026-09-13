import api from "../api/api";
import type { PublicWaitlistCreate, PublicWaitlistOffer } from "../types/waitlist";

export async function crearWaitlistPublica(slug: string, payload: PublicWaitlistCreate): Promise<{ message: string }> {
  return (await api.post<{ message: string }>(`/public/profesionales/${slug}/waitlist`, payload)).data;
}

export async function obtenerOfertaWaitlist(token: string): Promise<PublicWaitlistOffer> {
  return (await api.get<PublicWaitlistOffer>(`/public/waitlist/offers/${token}`)).data;
}

export async function aceptarOfertaWaitlist(token: string): Promise<PublicWaitlistOffer> {
  return (await api.post<PublicWaitlistOffer>(`/public/waitlist/offers/${token}/accept`)).data;
}
