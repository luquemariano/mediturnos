import api from "../api/api";
import type { Especialidad } from "../types/especialidad";


export async function obtenerEspecialidades():
Promise<Especialidad[]> {
  const respuesta = await api.get<Especialidad[]>(
    "/especialidades/",
  );

  return respuesta.data;
}
