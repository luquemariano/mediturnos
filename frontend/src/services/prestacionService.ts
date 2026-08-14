import api from "../api/api";
import type {
  Prestacion,
  PrestacionActualizar,
  PrestacionCrear,
} from "../types/prestacion";


export async function obtenerPrestaciones():
Promise<Prestacion[]> {
  const respuesta = await api.get<Prestacion[]>(
    "/prestaciones/",
  );

  return respuesta.data;
}

export async function obtenerMisPrestaciones(): Promise<Prestacion[]> {
  return (await api.get<Prestacion[]>("/profesionales/me/prestaciones")).data;
}

export async function crearMiPrestacion(datos: Omit<Prestacion, "id" | "profesional_id" | "activa" | "descripcion">): Promise<Prestacion> {
  return (await api.post<Prestacion>("/profesionales/me/prestaciones", datos)).data;
}

export async function editarMiPrestacion(id: number, datos: Partial<Pick<Prestacion, "nombre" | "duracion_minutos" | "precio" | "modalidad" | "activa">>): Promise<Prestacion> {
  return (await api.patch<Prestacion>(`/profesionales/me/prestaciones/${id}`, datos)).data;
}

export async function desactivarMiPrestacion(id: number): Promise<Prestacion> {
  return (await api.delete<Prestacion>(`/profesionales/me/prestaciones/${id}`)).data;
}


export async function crearPrestacion(
  datos: PrestacionCrear,
): Promise<Prestacion> {
  const respuesta = await api.post<Prestacion>(
    "/prestaciones/",
    datos,
  );

  return respuesta.data;
}


export async function actualizarPrestacion(
  prestacionId: number,
  datos: PrestacionActualizar,
): Promise<Prestacion> {
  const respuesta = await api.patch<Prestacion>(
    `/prestaciones/${prestacionId}`,
    datos,
  );

  return respuesta.data;
}
