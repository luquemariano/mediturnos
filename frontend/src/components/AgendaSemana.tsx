import { useMemo } from "react";
import type { CSSProperties } from "react";
import type { Turno } from "../types/turno";
import { claveFechaNegocio, formatearHoraTurno } from "../utils/fechaTurno";
import { distribuirSolapamientos, diasSemana, formatearFechaCivil, formatearSemana, hoyNegocio, minutosDesdeMedianoche, type FechaCivil } from "../utils/calendario";
import type { MarcaExcepcion } from "../utils/excepcionesAgenda";
import { etiquetaExcepcion } from "../utils/excepcionesAgenda";

type Props = { turnos: Turno[]; excepciones?: Map<FechaCivil, MarcaExcepcion>; fecha: FechaCivil; ahora: Date; onSeleccionarDia: (fecha: FechaCivil) => void; onSeleccionarTurno: (turno: Turno) => void };
const BASE_INICIO = 8 * 60;
const BASE_FIN = 20 * 60;
const ESCALA = 64 / 60;

function finMinutos(turno: Turno, inicio: number) {
  return turno.fecha_fin ? minutosDesdeMedianoche(turno.fecha_fin) : inicio + 30;
}
function esDomingo(fecha: string) { return new Date(`${fecha}T12:00:00Z`).getUTCDay() === 0; }

export default function AgendaSemana({ turnos, excepciones = new Map(), fecha, ahora, onSeleccionarDia, onSeleccionarTurno }: Props) {
  const dias = diasSemana(fecha);
  const porDia = useMemo(() => new Map(dias.map((dia) => [dia, turnos.filter((turno) => claveFechaNegocio(turno.fecha_hora) === dia)])), [dias, turnos]);
  const inicio = Math.floor(Math.min(BASE_INICIO, ...turnos.map((turno) => minutosDesdeMedianoche(turno.fecha_hora))) / 60) * 60;
  const fin = Math.ceil(Math.max(BASE_FIN, ...turnos.map((turno) => finMinutos(turno, minutosDesdeMedianoche(turno.fecha_hora)))) / 60) * 60;
  const filas = Array.from({ length: Math.max(1, (fin - inicio) / 60) }, (_, i) => inicio + i * 60);
  const hoy = hoyNegocio(ahora);
  const horaActual = minutosDesdeMedianoche(ahora.toISOString());
  return <section className="agenda-semana" aria-label={`Semana ${formatearSemana(fecha)}`}>
    <div className="agenda-semana-movil-dias" role="group" aria-label="Días de la semana">
      {dias.map((dia) => <button key={dia} type="button" aria-pressed={dia === fecha} onClick={() => onSeleccionarDia(dia)}>{new Intl.DateTimeFormat("es-AR", { weekday: "short", day: "numeric", timeZone: "UTC" }).format(new Date(`${dia}T12:00:00Z`))}</button>)}
    </div>
    <div className="agenda-semana-grid" style={{ "--filas": filas.length, "--alto": `${(fin - inicio) * ESCALA}px` } as CSSProperties}>
      <div className="agenda-semana-horas">{filas.map((min) => <span key={min} style={{ top: `${(min - inicio) * ESCALA}px` }}>{String(Math.floor(min / 60)).padStart(2, "0")}:00</span>)}</div>
      {dias.map((dia) => <div key={dia} className={`agenda-semana-columna${dia === hoy ? " es-hoy" : ""}${dia === fecha ? " es-seleccionada" : ""}${esDomingo(dia) ? " es-domingo" : ""}${excepciones.has(dia) ? ` es-excepcion es-${excepciones.get(dia)}` : ""}`}>
        <button type="button" className="agenda-semana-dia" onClick={() => onSeleccionarDia(dia)} aria-label={`Ver ${formatearFechaCivil(dia)}`}><strong>{new Intl.DateTimeFormat("es-AR", { weekday: "short", timeZone: "UTC" }).format(new Date(`${dia}T12:00:00Z`)).replace(".", "").toUpperCase()}</strong><span>{Number(dia.slice(8))}</span>{dia.slice(0, 7) !== fecha.slice(0, 7) && <small>{new Intl.DateTimeFormat("es-AR", { month: "short", timeZone: "UTC" }).format(new Date(`${dia}T12:00:00Z`)).replace(".", "").toUpperCase()}</small>}{dia === hoy && <small>Hoy</small>}{excepciones.has(dia) && <small>{etiquetaExcepcion(excepciones.get(dia))}</small>}</button>
        <div className="agenda-semana-pista" style={{ height: `${(fin - inicio) * ESCALA}px` }}>
          {Array.from({ length: filas.length - 1 }, (_, i) => <i key={i} style={{ top: `${(i + 1) * 60 * ESCALA}px` }} />)}
          {(() => { const items = porDia.get(dia) ?? []; const posiciones = distribuirSolapamientos(items.map((turno) => { const inicioTurno = minutosDesdeMedianoche(turno.fecha_hora); return { inicio: inicioTurno, fin: finMinutos(turno, inicioTurno) }; })); return items.map((turno, indice) => { const posicion = posiciones[indice]; const top = (posicion.inicio - inicio) * ESCALA; const height = Math.max(42, (posicion.fin - posicion.inicio) * ESCALA); const ancho = 100 / posicion.columnas; const gap = posicion.columnas > 1 ? 6 : 0; return <button key={turno.id} type="button" className={`agenda-semana-turno estado-${turno.estado}`} style={{ top, height, left: `calc(${posicion.columna * ancho}% + ${posicion.columna * gap / 2}px)`, width: `calc(${ancho}% - ${gap}px)` }} onClick={() => onSeleccionarTurno(turno)} title={`${formatearHoraTurno(turno.fecha_hora)} ${turno.paciente_nombre} · ${turno.prestacion_nombre}`} aria-label={`${formatearHoraTurno(turno.fecha_hora)}, ${turno.paciente_nombre}, ${turno.prestacion_nombre}, ${turno.estado}`}><strong>{formatearHoraTurno(turno.fecha_hora)}</strong><span>{turno.paciente_nombre}</span><small>{turno.prestacion_nombre}</small></button>; }); })()}
          {dia === hoy && horaActual >= inicio && horaActual <= fin && <b className="agenda-semana-ahora" style={{ top: `${(horaActual - inicio) * ESCALA}px` }} aria-label="Hora actual" />}
        </div>
      </div>)}
    </div>
  </section>;
}
