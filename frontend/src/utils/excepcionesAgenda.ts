import type { DisponibilidadExcepcion } from "../types/disponibilidad";
import type { FechaCivil } from "./calendario";

export type MarcaExcepcion = "vacaciones" | "cerrado" | "feriado";

export function marcaExcepcion(excepcion: DisponibilidadExcepcion): MarcaExcepcion | null {
  if (!excepcion.activa) return null;
  if (excepcion.origen === "vacaciones") return "vacaciones";
  if (excepcion.tipo === "cierre_dia") return excepcion.origen === "feriado" || excepcion.origen === "no_laborable" ? "feriado" : "cerrado";
  return excepcion.origen === "feriado" || excepcion.origen === "no_laborable" ? "feriado" : null;
}

export function mapaExcepciones(excepciones: DisponibilidadExcepcion[]): Map<FechaCivil, MarcaExcepcion> {
  const prioridad: Record<MarcaExcepcion, number> = { feriado: 1, cerrado: 2, vacaciones: 3 };
  const mapa = new Map<FechaCivil, MarcaExcepcion>();
  excepciones.forEach((excepcion) => { const marca = marcaExcepcion(excepcion); if (!marca) return; const fecha = excepcion.fecha as FechaCivil; if (!mapa.has(fecha) || prioridad[marca] > prioridad[mapa.get(fecha)!]) mapa.set(fecha, marca); });
  return mapa;
}

export function etiquetaExcepcion(marca?: MarcaExcepcion): string { return marca === "vacaciones" ? "Vacaciones" : marca === "cerrado" ? "Cerrado" : "Feriado"; }
