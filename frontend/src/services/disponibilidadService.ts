import api from "../api/api";
import type {
  Disponibilidad,
  DisponibilidadActualizar,
  DisponibilidadCrear,
  DisponibilidadExcepcion,
  DisponibilidadExcepcionCrear,
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

export async function obtenerMisExcepciones(fechaDesde: string): Promise<DisponibilidadExcepcion[]> {
  const respuesta = await api.get<DisponibilidadExcepcion[]>("/profesionales/me/excepciones-disponibilidad", { params: { fecha_desde: fechaDesde } });
  return respuesta.data;
}

export async function crearMiExcepcion(datos: DisponibilidadExcepcionCrear): Promise<DisponibilidadExcepcion> {
  const respuesta = await api.post<DisponibilidadExcepcion>("/profesionales/me/excepciones-disponibilidad", datos);
  return respuesta.data;
}

export async function eliminarMiExcepcion(id: number): Promise<DisponibilidadExcepcion> {
  const respuesta = await api.delete<DisponibilidadExcepcion>(`/profesionales/me/excepciones-disponibilidad/${id}`);
  return respuesta.data;
}
