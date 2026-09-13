export type WaitlistState = "activa" | "ofertada" | "reservada" | "cancelada" | "vencida";

export interface WaitlistEntry {
  id: number;
  identificador_publico: string;
  paciente_id: number;
  paciente_nombre: string;
  prestacion_id: number;
  prestacion_nombre: string;
  fecha_desde: string;
  fecha_hasta: string;
  hora_desde: string | null;
  hora_hasta: string | null;
  estado: WaitlistState;
  origen: "profesional" | "publico";
  created_at: string;
  updated_at: string;
}

export interface PublicWaitlistCreate {
  prestacion: string;
  fecha_desde: string;
  fecha_hasta: string;
  hora_desde?: string;
  hora_hasta?: string;
  paciente: { nombre: string; apellido: string; email: string; telefono: string; dni: string };
}

export interface PublicWaitlistOffer {
  estado: "activa" | "aceptada" | "vencida" | "cancelada";
  profesional: string;
  prestacion: string;
  fecha_hora: string;
  expires_at: string;
  paciente: string;
}
