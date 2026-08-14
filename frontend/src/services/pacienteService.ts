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

export async function buscarPacientesProfesional(q = ""): Promise<PacienteSeleccion[]> {
  const respuesta = await api.get<PacienteSeleccion[]>("/profesionales/me/pacientes", { params: q ? { q } : {} });
  return respuesta.data;
}

export async function crearPacienteProfesional(datos: Omit<PacienteSeleccion, "id">): Promise<PacienteSeleccion> {
  return (await api.post<PacienteSeleccion>("/profesionales/me/pacientes", datos)).data;
}

export async function editarPacienteProfesional(id: number, datos: Partial<Omit<PacienteSeleccion, "id">>): Promise<PacienteSeleccion> {
  return (await api.patch<PacienteSeleccion>(`/profesionales/me/pacientes/${id}`, datos)).data;
}

export async function desactivarPacienteProfesional(id: number): Promise<void> {
  await api.delete(`/profesionales/me/pacientes/${id}`);
}

export async function obtenerHistorialPaciente(id: number) {
  return (await api.get<Array<{id:number; fecha_hora:string; prestacion_nombre:string; estado:string; observaciones:string|null}>>(`/profesionales/me/pacientes/${id}/turnos`)).data;
}
