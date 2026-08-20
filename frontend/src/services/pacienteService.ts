import api from "../api/api";
import type {
  Paciente,
  PacienteCrear,
  PacienteSeleccion,
  EvolucionClinica,
  ClinicalProfile,
  ClinicalProfileUpdate,
  PatientDocument,
  PatientDocumentCategory,
  StudyRequest,
  StudyRequestStatus,
  PendingReviewResponse,
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

export async function obtenerEvolucionesPaciente(id: number): Promise<EvolucionClinica[]> {
  return (await api.get<EvolucionClinica[]>(`/pacientes/${id}/evoluciones`)).data;
}

export async function crearEvolucionPaciente(id: number, contenido: string): Promise<EvolucionClinica> {
  return (await api.post<EvolucionClinica>(`/pacientes/${id}/evoluciones`, { contenido })).data;
}
export async function getClinicalProfile(patientId: number): Promise<ClinicalProfile> { return (await api.get<ClinicalProfile>(`/pacientes/${patientId}/clinical-profile`)).data; }
export async function updateClinicalProfile(patientId: number, payload: ClinicalProfileUpdate): Promise<ClinicalProfile> { return (await api.put<ClinicalProfile>(`/pacientes/${patientId}/clinical-profile`, payload)).data; }
export async function listarDocumentosPaciente(patientId: number): Promise<PatientDocument[]> { return (await api.get<PatientDocument[]>(`/pacientes/${patientId}/documents`)).data; }
export async function crearIntentDocumento(patientId: number, payload: { filename: string; mime_type: string; size_bytes: number; category: PatientDocumentCategory }) { return (await api.post<{ document_id: number; upload_url: string; expires_in_seconds: number; required_content_type: string }>(`/pacientes/${patientId}/documents/upload-intents`, payload)).data; }
export async function confirmarDocumento(patientId: number, documentId: number): Promise<PatientDocument> { return (await api.post<PatientDocument>(`/pacientes/${patientId}/documents/${documentId}/confirm`)).data; }
export async function obtenerUrlDocumento(patientId: number, documentId: number): Promise<string> { return (await api.post<{ download_url: string }>(`/pacientes/${patientId}/documents/${documentId}/download-url`)).data.download_url; }
export async function eliminarDocumento(patientId: number, documentId: number): Promise<void> { await api.delete(`/pacientes/${patientId}/documents/${documentId}`); }
export async function listarStudyRequests(patientId: number, status?: StudyRequestStatus): Promise<StudyRequest[]> { return (await api.get<StudyRequest[]>(`/pacientes/${patientId}/study-requests`, { params: status ? { status } : {} })).data; }
export async function crearStudyRequest(patientId: number, payload: { title: string; instructions: string | null; turno_id: number | null; expires_at: string | null }): Promise<StudyRequest> { return (await api.post<StudyRequest>(`/pacientes/${patientId}/study-requests`, payload)).data; }
export async function cancelarStudyRequest(patientId: number, requestId: number): Promise<StudyRequest> { return (await api.post<StudyRequest>(`/pacientes/${patientId}/study-requests/${requestId}/cancel`)).data; }
export async function cerrarStudyRequest(patientId: number, requestId: number): Promise<StudyRequest> { return (await api.post<StudyRequest>(`/pacientes/${patientId}/study-requests/${requestId}/close`)).data; }
export async function generarStudyAccessLink(patientId: number, requestId: number): Promise<{ url: string; expires_in_seconds: number }> { return (await api.post<{ url: string; expires_in_seconds: number }>(`/pacientes/${patientId}/study-requests/${requestId}/access-link`)).data; }
export async function listarEstudiosPendientesRevision(): Promise<PendingReviewResponse> { return (await api.get<PendingReviewResponse>("/profesionales/me/study-requests/pending-review")).data; }
