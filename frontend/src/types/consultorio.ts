export interface ConsultorioAdministrado {
  id: number;
  nombre: string;
  zona_horaria: string;
  duracion_modulo_minutos: number;
  horizonte_materializacion_dias: number;
  estado: string;
}

export interface SalaConsultorio {
  id: number;
  consultorio_id: number;
  nombre: string;
  codigo: string;
  estado: string;
}

export interface ProfesionalConsultorio {
  profesional_id: number;
  nombre: string;
  estado: "preparatorio" | "activo";
}

export interface ModuloConsultorio {
  id: number;
  sala_id: number;
  sala_nombre: string;
  profesional_id: number | null;
  profesional_nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  fecha_origen: string | null;
  estado: "activa" | "suspendida" | "cancelada";
  origen: "recurrente" | "extraordinaria" | "excepcion";
}

export interface ReglaModuloConsultorio {
  id: number;
  sala_id: number;
  sala_nombre: string;
  profesional_id: number | null;
  profesional_nombre: string;
  invitacion_pendiente: boolean;
  dia_semana: number;
  hora_inicio: string;
  duracion_minutos: number;
  zona_horaria: string;
  vigente_desde: string;
  vigente_hasta: string | null;
  estado: string;
}

export interface InvitacionConsultorio {
  id: number;
  email: string;
  nombre_visible: string | null;
  estado: "preparacion" | "pendiente" | "aceptada" | "revocada" | "expirada";
  vence_en: string | null;
  modulos_reservados: number;
}

export interface ModuloSemanalPayload {
  sala_id: number;
  dia_semana: number;
  hora_inicio: string;
  duracion_minutos: number;
  vigente_desde: string;
  vigente_hasta?: string | null;
}
