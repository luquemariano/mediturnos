export interface Especialidad {
  id: number;
  nombre: string;
  descripcion: string | null;
  duracion_turno_minutos: number;
  activa: boolean;
}

export interface EspecialidadCrear {
  nombre: string;
  descripcion?: string | null;
  duracion_turno_minutos: number;
}

export interface EspecialidadActualizar {
  nombre?: string;
  descripcion?: string | null;
  duracion_turno_minutos?: number;
  activa?: boolean;
}
