import api from "../api/api";
import type { ReservaOnlineConfig, PrestacionReservaOnline } from "../types/reservaOnline";

export const obtenerReservaOnline = async () => (await api.get<ReservaOnlineConfig>("/profesionales/me/reserva-online")).data;
export const actualizarReservaOnline = async (reserva_online_activa: boolean) => (await api.patch<ReservaOnlineConfig>("/profesionales/me/reserva-online", { reserva_online_activa })).data;
export const actualizarHabilitacionOnline = async (identificador: string, habilitada_online: boolean) => (await api.patch<PrestacionReservaOnline>(`/prestaciones/${identificador}/reserva-online`, { habilitada_online })).data;
