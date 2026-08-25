import api from "../api/api";
import type {
  Profesional,
  ProfesionalActualizar,
  ProfesionalCrear,
} from "../types/profesional";


export async function obtenerProfesionales():
Promise<Profesional[]> {
  const respuesta = await api.get<Profesional[]>(
    "/profesionales/",
  );

  return respuesta.data;
}

export async function obtenerMiPerfilProfesional(): Promise<Profesional> {
  const respuesta = await api.get<Profesional>("/profesionales/me");
  return respuesta.data;
}

export async function actualizarMiPerfil(datos: ProfesionalActualizar): Promise<Profesional> {
  return (await api.patch<Profesional>("/profesionales/me", datos)).data;
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


export async function actualizarProfesional(
  profesionalId: number,
  datos: ProfesionalActualizar,
): Promise<Profesional> {
  const respuesta = await api.patch<Profesional>(
    `/profesionales/${profesionalId}`,
    datos,
  );

  return respuesta.data;
}
