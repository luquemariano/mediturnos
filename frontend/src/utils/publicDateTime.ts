export const ZONA_HORARIA_NEGOCIO = "America/Argentina/Buenos_Aires";

export function formatoHoraPublica(valor: string): string {
  return new Intl.DateTimeFormat("es-AR", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: ZONA_HORARIA_NEGOCIO }).format(new Date(valor));
}

export function formatoFechaHoraPublica(valor: string): string {
  return new Intl.DateTimeFormat("es-AR", { weekday: "long", day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit", hour12: false, timeZone: ZONA_HORARIA_NEGOCIO }).format(new Date(valor));
}
