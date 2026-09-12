export interface PrestacionReservaOnline {
  identificador_publico: string;
  nombre: string;
  activa: boolean;
  habilitada_online: boolean;
  duracion_minutos?: number;
  modalidad?: string;
}

export interface ReservaOnlineConfig {
  reserva_online_activa: boolean;
  slug_publico: string | null;
  url_publica: string | null;
  especialidades: Array<{ nombre: string }>;
  prestaciones: PrestacionReservaOnline[];
}
