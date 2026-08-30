import { claveFechaNegocio, fechaActualNegocio } from "./fechaTurno";

export type FechaCivil = `${number}-${number}-${number}`;

function fechaCivil(fecha: Date): FechaCivil {
  return fecha.toISOString().slice(0, 10) as FechaCivil;
}

function parsear(fecha: string): Date {
  const [anio, mes, dia] = fecha.split("-").map(Number);
  return new Date(Date.UTC(anio, mes - 1, dia, 12));
}

function ajustar(fecha: string, dias: number): FechaCivil {
  const resultado = parsear(fecha);
  resultado.setUTCDate(resultado.getUTCDate() + dias);
  return fechaCivil(resultado);
}

export function hoyNegocio(ahora = new Date()): FechaCivil { return fechaActualNegocio(ahora) as FechaCivil; }
export function formatearFechaCivil(fecha: string): string {
  return new Intl.DateTimeFormat("es-AR", { weekday: "long", day: "numeric", month: "long", year: "numeric", timeZone: "UTC" })
    .format(parsear(fecha)).replace(/^./, (letra) => letra.toUpperCase());
}
export function diaAnterior(fecha: string): FechaCivil { return ajustar(fecha, -1); }
export function diaSiguiente(fecha: string): FechaCivil { return ajustar(fecha, 1); }

export function inicioSemana(fecha: string): FechaCivil {
  const dia = parsear(fecha).getUTCDay();
  return ajustar(fecha, dia === 0 ? -6 : 1 - dia);
}
export function finSemana(fecha: string): FechaCivil { return ajustar(inicioSemana(fecha), 6); }
export function diasSemana(fecha: string): FechaCivil[] {
  const inicio = inicioSemana(fecha);
  return Array.from({ length: 7 }, (_, indice) => ajustar(inicio, indice));
}
export function semanaAnterior(fecha: string): FechaCivil { return ajustar(inicioSemana(fecha), -7); }
export function semanaSiguiente(fecha: string): FechaCivil { return ajustar(inicioSemana(fecha), 7); }
export function minutosDesdeMedianoche(fechaHora: string): number {
  const fecha = new Date(fechaHora);
  return fecha.getUTCHours() * 60 + fecha.getUTCMinutes();
}
export type IntervaloVisual = { inicio: number; fin: number; columna: number; columnas: number };
export function distribuirSolapamientos(intervalos: Array<{ inicio: number; fin: number }>): IntervaloVisual[] {
  const resultado: IntervaloVisual[] = [];
  const grupos: Array<Array<{ inicio: number; fin: number; indice: number }>> = [];
  intervalos.forEach((intervalo, indice) => {
    const grupo = grupos.find((items) => items.some((item) => intervalo.inicio < item.fin && item.inicio < intervalo.fin));
    if (grupo) grupo.push({ ...intervalo, indice }); else grupos.push([{ ...intervalo, indice }]);
  });
  grupos.forEach((grupo) => {
    const columnas: number[] = [];
    grupo.sort((a, b) => a.inicio - b.inicio || a.fin - b.fin).forEach((intervalo) => {
      let columna = columnas.findIndex((fin) => fin <= intervalo.inicio);
      if (columna < 0) { columna = columnas.length; columnas.push(intervalo.fin); } else columnas[columna] = intervalo.fin;
      resultado[intervalo.indice] = { ...intervalo, columna, columnas: Math.max(columnas.length, grupo.length) };
    });
    grupo.forEach((intervalo) => { resultado[intervalo.indice].columnas = columnas.length; });
  });
  return resultado;
}
export function formatearSemana(fecha: string): string {
  const inicio = parsear(inicioSemana(fecha));
  const fin = parsear(finSemana(fecha));
  const opciones = { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" } as const;
  return `${new Intl.DateTimeFormat("es-AR", opciones).format(inicio)} - ${new Intl.DateTimeFormat("es-AR", opciones).format(fin)}`;
}

export function primerDiaMes(fecha: string): FechaCivil {
  const valor = parsear(fecha);
  return fechaCivil(new Date(Date.UTC(valor.getUTCFullYear(), valor.getUTCMonth(), 1, 12)));
}
export function ultimoDiaMes(fecha: string): FechaCivil {
  const valor = parsear(fecha);
  return fechaCivil(new Date(Date.UTC(valor.getUTCFullYear(), valor.getUTCMonth() + 1, 0, 12)));
}
export function mesAnterior(fecha: string): FechaCivil {
  const valor = parsear(fecha);
  return fechaCivil(new Date(Date.UTC(valor.getUTCFullYear(), valor.getUTCMonth() - 1, 1, 12)));
}
export function mesSiguiente(fecha: string): FechaCivil {
  const valor = parsear(fecha);
  return fechaCivil(new Date(Date.UTC(valor.getUTCFullYear(), valor.getUTCMonth() + 1, 1, 12)));
}

export function diasGrillaMes(fecha: string): FechaCivil[] {
  const inicio = inicioSemana(primerDiaMes(fecha));
  const fin = finSemana(ultimoDiaMes(fecha));
  const dias: FechaCivil[] = [];
  for (let actual = inicio; actual <= fin; actual = ajustar(actual, 1)) dias.push(actual);
  return dias;
}
export function formatearMes(fecha: string): string {
  return new Intl.DateTimeFormat("es-AR", { month: "long", year: "numeric", timeZone: "UTC" })
    .format(parsear(fecha)).replace(/^./, (letra) => letra.toUpperCase());
}

export function fechaTurnoEnDiaNegocio(fechaHora: string): FechaCivil {
  return claveFechaNegocio(fechaHora) as FechaCivil;
}
