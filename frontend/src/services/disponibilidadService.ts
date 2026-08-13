import api from "../api/api";
import type {
  Disponibilidad,
  DisponibilidadActualizar,
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

export async function actualizarMiDisponibilidad(
  disponibilidadId: number,
  datos: DisponibilidadActualizar,
): Promise<Disponibilidad> {
  const respuesta = await api.patch<Disponibilidad>(
    `/profesionales/me/disponibilidades/${disponibilidadId}`,
    datos,
  );
  return respuesta.data;
}

export async function eliminarMiDisponibilidad(
  disponibilidadId: number,
): Promise<Disponibilidad> {
  const respuesta = await api.delete<Disponibilidad>(
    `/profesionales/me/disponibilidades/${disponibilidadId}`,
  );
  return respuesta.data;
}
