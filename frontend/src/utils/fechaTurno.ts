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

function diasEntreClaves(desde: string, hasta: string): number {
  const [anioDesde, mesDesde, diaDesde] = desde.split("-").map(Number);
  const [anioHasta, mesHasta, diaHasta] = hasta.split("-").map(Number);
  return Math.round(
    (Date.UTC(anioHasta, mesHasta - 1, diaHasta) - Date.UTC(anioDesde, mesDesde - 1, diaDesde))
    / 86_400_000,
  );
}

export function etiquetaFechaProximoTurno(
  fechaHora: string,
  ahora: Date = new Date(),
): string {
  const fechaTurno = new Date(fechaHora);
  const diferenciaDias = diasEntreClaves(
    fechaActualNegocio(ahora),
    claveFechaNegocio(fechaHora),
  );

  if (diferenciaDias === 0) return "HOY";
  if (diferenciaDias === 1) return "MAÑANA";

  const opciones = diferenciaDias >= 2 && diferenciaDias <= 6
    ? { weekday: "long", day: "numeric" } as const
    : { day: "numeric", month: "short" } as const;

  return new Intl.DateTimeFormat("es-AR", {
    timeZone: ZONA_HORARIA_NEGOCIO,
    ...opciones,
  }).format(fechaTurno).replace(".", "").toUpperCase();
}
