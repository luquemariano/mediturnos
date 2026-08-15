export interface Profesional {
  id: number;
  nombre: string;
  apellido: string;
  matricula: string;
  telefono: string | null;
  email: string | null;
  activo: boolean;
  onboarding_step: import("./auth").OnboardingStep;
  especialidades: EspecialidadProfesional[];
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
  especialidades?: EspecialidadProfesionalCrear[];
}
