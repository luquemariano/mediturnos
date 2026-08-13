import api from "../api/api";
import type {
  Disponibilidad,
  DisponibilidadActualizar,
  DisponibilidadCrear,
  DisponibilidadExcepcion,
  DisponibilidadExcepcionCrear,
  DisponibilidadExcepcionRango,
  DisponibilidadExcepcionRangoCreado,
  DisponibilidadExcepcionRangoReabierto,
  FeriadoCrear,
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

export async function cerrarMiDisponibilidadPorRango(datos: DisponibilidadExcepcionRango): Promise<DisponibilidadExcepcionRangoCreado> {
  const respuesta = await api.post<DisponibilidadExcepcionRangoCreado>("/profesionales/me/excepciones-disponibilidad/rango", datos);
  return respuesta.data;
}

export async function reabrirMiDisponibilidadPorRango(datos: DisponibilidadExcepcionRango): Promise<DisponibilidadExcepcionRangoReabierto> {
  const respuesta = await api.post<DisponibilidadExcepcionRangoReabierto>("/profesionales/me/excepciones-disponibilidad/reabrir-rango", datos);
  return respuesta.data;
}

export async function crearMiFeriado(datos: FeriadoCrear): Promise<DisponibilidadExcepcion> {
  const respuesta = await api.post<DisponibilidadExcepcion>("/profesionales/me/feriados", datos);
  return respuesta.data;
}

export async function eliminarMiFeriado(id: number): Promise<DisponibilidadExcepcion> {
  const respuesta = await api.delete<DisponibilidadExcepcion>(`/profesionales/me/feriados/${id}`);
  return respuesta.data;
}
