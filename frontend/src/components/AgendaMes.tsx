import type { Turno } from "../types/turno";
import { claveFechaNegocio } from "../utils/fechaTurno";
import { diasGrillaMes, formatearMes, hoyNegocio, type FechaCivil } from "../utils/calendario";

type Props = { turnos: Turno[]; fecha: FechaCivil; ahora: Date; onSeleccionarDia: (fecha: FechaCivil) => void };

export default function AgendaMes({ turnos, fecha, ahora, onSeleccionarDia }: Props) {
  const dias = diasGrillaMes(fecha);
  const mes = fecha.slice(0, 7);
  const hoy = hoyNegocio(ahora);
  return <section className="agenda-mes" aria-label={`Calendario de ${formatearMes(fecha)}`}>
    <div className="agenda-mes-semana" role="row">{["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"].map((dia) => <strong key={dia} role="columnheader">{dia}</strong>)}</div>
    <div className="agenda-mes-grilla" role="grid" aria-label={`Calendario de ${formatearMes(fecha)}`}>
      {dias.map((dia) => { const delDia = turnos.filter((turno) => claveFechaNegocio(turno.fecha_hora) === dia); const cantidad = delDia.length; const esContexto = !dia.startsWith(mes); const esHoy = dia === hoy; return <button key={dia} type="button" className={`agenda-mes-celda${esContexto ? " es-contexto" : ""}${esHoy ? " es-hoy" : ""}${cantidad ? " tiene-turnos" : ""}`} onClick={() => onSeleccionarDia(dia)} aria-label={`${esHoy ? "Hoy, " : ""}${new Intl.DateTimeFormat("es-AR", { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" }).format(new Date(`${dia}T12:00:00Z`))}, ${cantidad} ${cantidad === 1 ? "turno" : "turnos"}`}>
        <span>{Number(dia.slice(8))}</span>{esHoy && <small>Hoy</small>}{cantidad > 0 && <><em>{cantidad} {cantidad === 1 ? "turno" : "turnos"}</em><div className="agenda-mes-previews">{delDia.slice(0, 2).map((turno) => <i key={turno.id}>{new Intl.DateTimeFormat("es-AR", { hour: "2-digit", minute: "2-digit", timeZone: "America/Argentina/Buenos_Aires" }).format(new Date(turno.fecha_hora))} · {turno.paciente_nombre}</i>)}{cantidad > 2 && <i>+{cantidad - 2} más</i>}</div></>}
      </button>; })}
    </div>
    {turnos.length === 0 && <p className="agenda-mes-vacio">No hay turnos programados este mes.</p>}
  </section>;
}
