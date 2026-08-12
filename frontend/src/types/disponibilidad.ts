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
