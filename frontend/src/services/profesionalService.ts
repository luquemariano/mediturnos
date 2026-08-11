import api from "../api/api";
import type {
  Profesional,
  ProfesionalCrear,
} from "../types/profesional";


export async function obtenerProfesionales():
Promise<Profesional[]> {
  const respuesta = await api.get<Profesional[]>(
    "/profesionales/",
  );

  return respuesta.data;
}


export async function crearProfesional(
  datos: ProfesionalCrear,
): Promise<Profesional> {
  const respuesta = await api.post<Profesional>(
    "/profesionales/",
    datos,
  );

  return respuesta.data;
}
