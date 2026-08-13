import api from "../api/api";
import type {
  Paciente,
  PacienteCrear,
  PacienteSeleccion,
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

export async function obtenerMiPerfilPaciente(): Promise<Paciente> {
  const respuesta = await api.get<Paciente>("/pacientes/me");
  return respuesta.data;
}

export async function obtenerPacientesParaProfesional(): Promise<PacienteSeleccion[]> {
  const respuesta = await api.get<PacienteSeleccion[]>("/profesionales/me/pacientes");
  return respuesta.data;
}
