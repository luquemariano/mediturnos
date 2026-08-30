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

export function fechaTurnoEnDiaNegocio(fechaHora: string): FechaCivil {
  return claveFechaNegocio(fechaHora) as FechaCivil;
}
