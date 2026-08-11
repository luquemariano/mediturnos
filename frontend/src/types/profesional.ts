export interface Profesional {
  id: number;
  nombre: string;
  apellido: string;
  matricula: string;
  telefono: string | null;
  email: string | null;
  activo: boolean;
}

export interface EspecialidadProfesionalCrear {
  especialidad_id: number;
  duracion_turno_minutos: number;
}

export interface ProfesionalCrear {
  nombre: string;
  apellido: string;
  matricula: string;
  telefono?: string;
  email?: string;
  especialidades: EspecialidadProfesionalCrear[];
}

export interface ProfesionalActualizar {
  nombre?: string;
  apellido?: string;
  matricula?: string;
  telefono?: string | null;
  email?: string | null;
}
