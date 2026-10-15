import api from "../api/api";
import type { ActividadProfesional } from "../types/profesional";

export async function obtenerActividadesProfesionales(): Promise<ActividadProfesional[]> {
  return (await api.get<ActividadProfesional[]>("/catalogo/actividades-profesionales")).data;
}
