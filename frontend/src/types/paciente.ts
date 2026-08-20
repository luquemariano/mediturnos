export interface Paciente {
  id: number;
  nombre: string;
  apellido: string;
  dni: string | null;
  fecha_nacimiento: string | null;
  telefono: string | null;
  email: string | null;
  obra_social: string | null;
  numero_afiliado: string | null;
  activo: boolean;
}

export interface PacienteCrear {
  nombre: string;
  apellido: string;
  dni: string | null;
  fecha_nacimiento: string | null;
  telefono: string | null;
  email: string | null;
  obra_social: string | null;
  numero_afiliado: string | null;
}

export interface PacienteSeleccion {
  id: number;
  nombre: string;
  apellido: string;
  dni: string | null;
  telefono: string | null;
  email: string | null;
  fecha_nacimiento: string | null;
}

export interface EvolucionClinica {
  id: number;
  paciente_id: number;
  profesional_id: number;
  profesional_nombre: string;
  contenido: string;
  created_at: string;
}
export interface ClinicalProfile { id: number | null; paciente_id: number; antecedentes: string | null; alergias: string | null; medicacion_habitual: string | null; condiciones_relevantes: string | null; observaciones: string | null; updated_at: string | null; updated_by_profesional_id: number | null; }
export type ClinicalProfileUpdate = Omit<ClinicalProfile, "id" | "paciente_id" | "updated_at" | "updated_by_profesional_id">;
export type PatientDocumentCategory = "laboratory" | "imaging" | "order" | "report" | "prescription" | "other";
export interface PatientDocument { id: number; paciente_id: number; original_filename: string; mime_type: string; size_bytes: number | null; category: PatientDocumentCategory; status: "available"; created_at: string; available_at: string | null; uploaded_by_profesional_id: number | null; }
export type StudyRequestStatus = "pending" | "submitted" | "reviewed" | "closed" | "cancelled";
export interface StudyRequest { id: number; paciente_id: number; profesional_id: number; turno_id: number | null; title: string; instructions: string | null; status: StudyRequestStatus; requested_at: string; expires_at: string | null; submitted_at: string | null; reviewed_at: string | null; closed_at: string | null; cancelled_at: string | null; created_at: string; updated_at: string; }
