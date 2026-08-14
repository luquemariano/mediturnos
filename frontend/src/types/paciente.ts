export interface Paciente {
  id: number;
  nombre: string;
  apellido: string;
  dni: string | null;
  fecha_nacimiento: string | null;
  telefono: string | null;
  email: string | null;
  obra_social: string | null;
  numero_afiliado: string | null;
  activo: boolean;
}

export interface PacienteCrear {
  nombre: string;
  apellido: string;
  dni: string | null;
  fecha_nacimiento: string | null;
  telefono: string | null;
  email: string | null;
  obra_social: string | null;
  numero_afiliado: string | null;
}

export interface PacienteSeleccion {
  id: number;
  nombre: string;
  apellido: string;
  dni: string | null;
  telefono: string | null;
  email: string | null;
  fecha_nacimiento: string | null;
}
