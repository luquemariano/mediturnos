import api from "../api/api";
import type {
  Disponibilidad,
  DisponibilidadCrear,
} from "../types/disponibilidad";

export async function obtenerDisponibilidades(): Promise<Disponibilidad[]> {
  const respuesta = await api.get<Disponibilidad[]>("/disponibilidades/");
  return respuesta.data;
}

export async function obtenerDisponibilidadesProfesional(
  profesionalId: number,
): Promise<Disponibilidad[]> {
  const respuesta = await api.get<Disponibilidad[]>(
    `/disponibilidades/profesional/${profesionalId}`,
  );
  return respuesta.data;
}

export async function crearDisponibilidad(
  datos: DisponibilidadCrear,
): Promise<Disponibilidad> {
  const respuesta = await api.post<Disponibilidad>("/disponibilidades/", datos);
  return respuesta.data;
}
