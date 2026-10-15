import api from "../api/api";
import type {
  ConsultorioAdministrado,
  InvitacionConsultorio,
  ModuloConsultorio,
  ModuloSemanalPayload,
  ProfesionalConsultorio,
  ReglaModuloConsultorio,
  SalaConsultorio,
} from "../types/consultorio";

export async function listarConsultoriosAdministrados() {
  return (await api.get<ConsultorioAdministrado[]>("/consultorios")).data;
}

export async function listarSalasConsultorio(id: number) {
  return (await api.get<SalaConsultorio[]>(`/consultorios/${id}/salas`)).data;
}

export async function listarProfesionalesConsultorio(id: number) {
  return (await api.get<ProfesionalConsultorio[]>(`/consultorios/${id}/profesionales`)).data;
}

export async function listarReglasConsultorio(id: number) {
  return (await api.get<ReglaModuloConsultorio[]>(`/consultorios/${id}/reglas-modulo`)).data;
}

export async function listarModulosConsultorio(id: number, desde: string, hasta: string) {
  return (await api.get<ModuloConsultorio[]>(`/consultorios/${id}/modulos`, { params: { desde, hasta } })).data;
}

export async function listarInvitacionesConsultorio(id: number) {
  return (await api.get<InvitacionConsultorio[]>(`/consultorios/${id}/invitaciones`)).data;
}

export async function crearReglaConsultorio(id: number, payload: ModuloSemanalPayload & { profesional_id: number }) {
  return (await api.post<ReglaModuloConsultorio>(`/consultorios/${id}/reglas-modulo`, payload)).data;
}

export async function actualizarReglaConsultorio(id: number, reglaId: number, payload: Record<string, unknown>) {
  return (await api.patch(`/consultorios/${id}/reglas-modulo/${reglaId}`, payload)).data;
}

export async function crearModuloExtraordinario(id: number, payload: { sala_id: number; profesional_id: number; fecha_inicio: string; fecha_fin: string }) {
  return (await api.post<ModuloConsultorio>(`/consultorios/${id}/modulos-extraordinarios`, payload)).data;
}

export async function actualizarModuloConsultorio(id: number, ocurrenciaId: number, payload: Record<string, unknown>) {
  return (await api.patch<ModuloConsultorio>(`/consultorios/${id}/modulos/${ocurrenciaId}`, payload)).data;
}

export async function suspenderModuloConsultorio(id: number, ocurrenciaId: number) {
  return (await api.post(`/consultorios/${id}/modulos/${ocurrenciaId}/suspender`)).data;
}

export async function crearInvitacionConsultorio(id: number, payload: { email: string; nombre_visible?: string; modulos: ModuloSemanalPayload[] }) {
  return (await api.post<InvitacionConsultorio>(`/consultorios/${id}/invitaciones`, payload)).data;
}

export async function enviarInvitacionConsultorio(id: number, invitacionId: number, reenviar = false) {
  const accion = reenviar ? "reenviar" : "enviar";
  return (await api.post(`/consultorios/${id}/invitaciones/${invitacionId}/${accion}`)).data;
}

export async function revocarInvitacionConsultorio(id: number, invitacionId: number) {
  return (await api.post(`/consultorios/${id}/invitaciones/${invitacionId}/revocar`)).data;
}
