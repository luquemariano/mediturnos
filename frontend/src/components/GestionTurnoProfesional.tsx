import { useState } from "react";
import axios from "axios";

import "./GestionTurnoProfesional.css";
import { obtenerHorariosLibres, reprogramarMiTurnoProfesional } from "../services/turnoService";
import type { HorarioLibre, Turno } from "../types/turno";
import { fechaActualNegocio, formatearFechaTurno, formatearHoraTurno } from "../utils/fechaTurno";
import { etiquetaEstado } from "../utils/estadoTurno";

type Props = {
  modo: "detalle" | "cancelar" | "reprogramar";
  turno: Turno;
  guardando?: boolean;
  errorExterno?: string;
  onCerrar: () => void;
  onCambiarModo: (modo: "cancelar" | "reprogramar") => void;
  onCancelar: () => Promise<void>;
  onReprogramado: (turno: Turno) => void;
};

function detalleError(error: unknown, alternativo: string) {
  if (axios.isAxiosError(error) && typeof error.response?.data?.detail === "string") {
    return error.response.data.detail;
  }
  return alternativo;
}

export default function GestionTurnoProfesional({
  modo,
  turno,
  guardando = false,
  errorExterno = "",
  onCerrar,
  onCambiarModo,
  onCancelar,
  onReprogramado,
}: Props) {
  const [fecha, setFecha] = useState("");
  const [horarios, setHorarios] = useState<HorarioLibre[]>([]);
  const [fechaHora, setFechaHora] = useState("");
  const [consultando, setConsultando] = useState(false);
  const [reprogramando, setReprogramando] = useState(false);
  const [error, setError] = useState("");

  async function consultar(nuevaFecha: string) {
    setFecha(nuevaFecha);
    setFechaHora("");
    setHorarios([]);
    setError("");
    if (!nuevaFecha) return;
    setConsultando(true);
    try {
      setHorarios(await obtenerHorariosLibres(turno.prestacion_id, nuevaFecha, turno.id));
    } catch (motivo) {
      setError(detalleError(motivo, "No pudimos consultar los horarios disponibles."));
    } finally {
      setConsultando(false);
    }
  }

  async function confirmarReprogramacion() {
    if (reprogramando || !fechaHora) return;
    setReprogramando(true);
    setError("");
    try {
      onReprogramado(await reprogramarMiTurnoProfesional(turno.id, fechaHora));
    } catch (motivo) {
      setError(detalleError(motivo, "No pudimos reprogramar el turno."));
      if (axios.isAxiosError(motivo) && motivo.response?.status === 409 && fecha) {
        try {
          setHorarios(await obtenerHorariosLibres(turno.prestacion_id, fecha, turno.id));
          setFechaHora("");
        } catch {
          setHorarios([]);
        }
      }
    } finally {
      setReprogramando(false);
    }
  }

  const ocupado = guardando || reprogramando;
  return <div className="gestion-turno-fondo" role="presentation">
    <section className="gestion-turno" role="dialog" aria-modal="true" aria-labelledby="gestion-turno-titulo">
      <header>
        <div><span>MI AGENDA</span><h2 id="gestion-turno-titulo">{modo === "detalle" ? "Detalle del turno" : modo === "cancelar" ? "Cancelar turno" : "Reprogramar turno"}</h2></div>
        <button type="button" aria-label="Cerrar" disabled={ocupado} onClick={onCerrar}>×</button>
      </header>
      <div className="gestion-turno-cuerpo">
        <dl>
          <div><dt>Paciente</dt><dd>{turno.paciente_nombre}</dd></div>
          <div><dt>Prestación</dt><dd>{turno.prestacion_nombre}</dd></div>
          <div><dt>Fecha actual</dt><dd>{formatearFechaTurno(turno.fecha_hora)}</dd></div>
          <div><dt>Hora actual</dt><dd>{formatearHoraTurno(turno.fecha_hora)}</dd></div>
          {modo === "detalle" && <div><dt>Estado</dt><dd>{etiquetaEstado(turno.estado)}</dd></div>}
        </dl>

        {modo === "detalle" ? <p>Revisá los datos del turno y elegí una acción.</p>
        : modo === "cancelar" ? <p className="gestion-turno-aviso">El turno quedará cancelado. Los pagos existentes no se eliminan ni se reembolsan automáticamente.</p>
        : <div className="gestion-turno-reprogramar">
          <label>Nueva fecha
            <input type="date" min={fechaActualNegocio()} value={fecha} disabled={ocupado} onChange={(evento) => void consultar(evento.target.value)} />
          </label>
          <fieldset disabled={ocupado || consultando || !fecha}>
            <legend>Nuevo horario</legend>
            {consultando && <p role="status">Consultando horarios…</p>}
            {!consultando && fecha && horarios.length === 0 && <p>No hay horarios disponibles para esta fecha.</p>}
            <div className="gestion-turno-horarios">
              {horarios.map((horario) => <label key={horario.fecha_hora} className={fechaHora === horario.fecha_hora ? "seleccionado" : undefined}>
                <input type="radio" name="nuevo-horario" value={horario.fecha_hora} checked={fechaHora === horario.fecha_hora} onChange={(evento) => setFechaHora(evento.target.value)} />
                {formatearHoraTurno(horario.fecha_hora)}
              </label>)}
            </div>
          </fieldset>
        </div>}

        {(error || errorExterno) && <p className="gestion-turno-error" role="alert">{error || errorExterno}</p>}
      </div>
      <footer>
        <button type="button" disabled={ocupado} onClick={onCerrar}>Volver</button>
        {modo === "detalle" ? <>
          <button type="button" className="es-peligro" onClick={() => onCambiarModo("cancelar")}>Cancelar</button>
          <button type="button" onClick={() => onCambiarModo("reprogramar")}>Reprogramar</button>
        </> : modo === "cancelar"
          ? <button type="button" className="es-peligro" disabled={ocupado} onClick={() => void onCancelar()}>{guardando ? "Cancelando…" : "Cancelar turno"}</button>
          : <button type="button" disabled={ocupado || !fechaHora} onClick={() => void confirmarReprogramacion()}>{reprogramando ? "Reprogramando…" : "Confirmar cambio"}</button>}
      </footer>
    </section>
  </div>;
}
