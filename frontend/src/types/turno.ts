export type EstadoTurno =
  | "reservado"
  | "confirmado"
  | "cancelado"
  | "ausente"
  | "finalizado";

export interface Turno {
  id: number;

  paciente_id: number;
  paciente_nombre: string;

  prestacion_id: number;
  prestacion_nombre: string;

  profesional_nombre: string;
  especialidad_nombre: string;

  fecha_hora: string;
  estado: EstadoTurno;
  observaciones: string | null;
}

export interface TurnoCrear {
  paciente_id: number;
  prestacion_id: number;
  fecha_hora: string;
  observaciones: string | null;
}

export interface HorarioLibre {
  fecha_hora: string;
}
