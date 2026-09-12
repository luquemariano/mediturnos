import api from "../api/api";
import type { AdminAdoptionItem, FiltrosAdopcionAdmin } from "../types/adminAdoption";

export async function obtenerAdopcionAdmin(filtros: FiltrosAdopcionAdmin, signal?: AbortSignal): Promise<AdminAdoptionItem[]> {
  return (await api.get<AdminAdoptionItem[]>("/admin/adoption", { params: filtros, signal })).data;
}
