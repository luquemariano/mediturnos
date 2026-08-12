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
