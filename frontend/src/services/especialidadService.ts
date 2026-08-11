import api from "../api/api";
import type {
  Especialidad,
  EspecialidadActualizar,
  EspecialidadCrear,
} from "../types/especialidad";


export async function obtenerEspecialidades():
Promise<Especialidad[]> {
  const respuesta = await api.get<Especialidad[]>(
    "/especialidades/",
  );

  return respuesta.data;
}


export async function crearEspecialidad(
  datos: EspecialidadCrear,
): Promise<Especialidad> {
  const respuesta = await api.post<Especialidad>(
    "/especialidades/",
    datos,
  );

  return respuesta.data;
}


export async function actualizarEspecialidad(
  especialidadId: number,
  datos: EspecialidadActualizar,
): Promise<Especialidad> {
  const respuesta = await api.patch<Especialidad>(
    `/especialidades/${especialidadId}`,
    datos,
  );

  return respuesta.data;
}
