export interface Disponibilidad {
  id: number;
  profesional_id: number;
  dia_semana: number;
  hora_inicio: string;
  hora_fin: string;
  activa: boolean;
}

export interface DisponibilidadCrear {
  profesional_id: number;
  dia_semana: number;
  hora_inicio: string;
  hora_fin: string;
}

export interface DisponibilidadActualizar {
  dia_semana: number;
  hora_inicio: string;
  hora_fin: string;
}

export type TipoDisponibilidadExcepcion = "cierre_dia" | "franja_extraordinaria";
export interface DisponibilidadExcepcion { id: number; profesional_id: number; fecha: string; tipo: TipoDisponibilidadExcepcion; hora_inicio: string | null; hora_fin: string | null; activa: boolean; }
export interface DisponibilidadExcepcionCrear { fecha: string; tipo: TipoDisponibilidadExcepcion; hora_inicio?: string; hora_fin?: string; }
