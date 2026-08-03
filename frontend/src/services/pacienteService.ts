import api from "../api/api";
import type {
  Paciente,
  PacienteCrear,
} from "../types/paciente";

export async function obtenerPacientes():
Promise<Paciente[]> {
  const respuesta = await api.get<Paciente[]>(
    "/pacientes/",
  );

  return respuesta.data;
}

export async function crearPaciente(
  datos: PacienteCrear,
): Promise<Paciente> {
  const respuesta = await api.post<Paciente>(
    "/pacientes/",
    datos,
  );

  return respuesta.data;
}