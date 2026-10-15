export interface Profesional {
  id: number;
  nombre: string;
  apellido: string;
  matricula: string | null;
  actividad_profesional_id?: number | null;
  actividad_profesional?: ActividadProfesional | null;
  telefono: string | null;
  email: string | null;
  activo: boolean;
  onboarding_step: import("./auth").OnboardingStep;
  especialidades: EspecialidadProfesional[];
}

export interface ActividadProfesional {
  id: number;
  codigo: string;
  nombre: string;
  requiere_matricula: boolean;
  requiere_especialidad: boolean;
}

export interface EspecialidadProfesional {
  especialidad_id: number;
  duracion_turno_minutos: number | null;
}

export interface EspecialidadProfesionalCrear {
  especialidad_id: number;
  duracion_turno_minutos: number;
}

export interface ProfesionalCrear {
  nombre: string;
  apellido: string;
  actividad_profesional_id: number;
  matricula?: string;
  telefono?: string;
  email?: string;
  especialidades?: EspecialidadProfesionalCrear[];
}

export interface ProfesionalActualizar {
  nombre?: string;
  apellido?: string;
  matricula?: string | null;
  actividad_profesional_id?: number;
  telefono?: string | null;
  email?: string | null;
  especialidades?: EspecialidadProfesionalCrear[];
}
