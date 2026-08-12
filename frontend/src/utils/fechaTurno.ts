export const ZONA_HORARIA_NEGOCIO =
  "America/Argentina/Buenos_Aires";

function partesFecha(fecha: Date): Record<string, string> {
  const partes = new Intl.DateTimeFormat("en-US", {
    timeZone: ZONA_HORARIA_NEGOCIO,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(fecha);

  return Object.fromEntries(
    partes.map((parte) => [parte.type, parte.value]),
  );
}

export function claveFechaNegocio(fechaHora: string): string {
  const partes = partesFecha(new Date(fechaHora));
  return `${partes.year}-${partes.month}-${partes.day}`;
}

export function fechaActualNegocio(
  ahora: Date = new Date(),
): string {
  const partes = partesFecha(ahora);
  return `${partes.year}-${partes.month}-${partes.day}`;
}

export function formatearFechaTurno(fechaHora: string): string {
  return new Intl.DateTimeFormat("es-AR", {
    timeZone: ZONA_HORARIA_NEGOCIO,
    weekday: "long",
    day: "2-digit",
    month: "long",
    year: "numeric",
  }).format(new Date(fechaHora));
}

export function formatearHoraTurno(fechaHora: string): string {
  return new Intl.DateTimeFormat("es-AR", {
    timeZone: ZONA_HORARIA_NEGOCIO,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(fechaHora));
}

export function formatearFechaAgrupada(fecha: string): string {
  return formatearFechaTurno(`${fecha}T15:00:00Z`);
}
