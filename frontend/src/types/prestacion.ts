export type ModalidadPrestacion =
  | "presencial"
  | "virtual";


export interface Prestacion {
  id: number;
  nombre: string;
  descripcion: string | null;
  duracion_minutos: number;
  precio: number | string;
  modalidad: ModalidadPrestacion;
  activa: boolean;
  profesional_id: number;
  especialidad_id: number;
}


export interface PrestacionCrear {
  nombre: string;
  descripcion?: string | null;
  duracion_minutos: number;
  precio: number;
  modalidad: ModalidadPrestacion;
  profesional_id: number;
  especialidad_id: number;
}


export interface PrestacionActualizar {
  nombre?: string;
  descripcion?: string | null;
  duracion_minutos?: number;
  precio?: number;
  modalidad?: ModalidadPrestacion;
  activa?: boolean;
}
