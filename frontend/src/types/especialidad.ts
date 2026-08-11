export interface Especialidad {
  id: number;
  nombre: string;
  descripcion: string | null;
  duracion_turno_minutos: number;
  activa: boolean;
}
