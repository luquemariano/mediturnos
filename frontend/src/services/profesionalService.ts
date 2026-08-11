import api from "../api/api";
import type { Profesional } from "../types/profesional";


export async function obtenerProfesionales():
Promise<Profesional[]> {
  const respuesta = await api.get<Profesional[]>(
    "/profesionales/",
  );

  return respuesta.data;
}
