import { useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";

import {
  obtenerHorariosLibres,
  reprogramarTurno,
} from "../services/turnoService";
import type { HorarioLibre, Turno } from "../types/turno";
import {
  fechaActualNegocio,
  formatearFechaTurno,
  formatearHoraTurno,
} from "../utils/fechaTurno";

type ModalReprogramarTurnoProps = {
  turno: Turno;
  onCerrar: () => void;
  onTurnoReprogramado: (turno: Turno) => void;
};

function obtenerMensajeError(
  error: unknown,
  alternativo: string,
): string {
  if (!axios.isAxiosError(error)) {
    return "Ocurrió un error inesperado.";
  }

  const estado = error.response?.status;
  const detalle = error.response?.data?.detail;

  if (estado === 401) {
    return "La sesión venció o no es válida. Iniciá sesión nuevamente.";
  }
  if (estado === 403) {
    return "No tenés permisos para reprogramar este turno.";
  }
  if (estado === 404) {
    return typeof detalle === "string"
      ? detalle
      : "No se encontró el turno o la prestación.";
  }
  if (estado === 400 && typeof detalle === "string") {
    return detalle;
  }
  if (estado === 422 && Array.isArray(detalle)) {
    return detalle
      .map((item) => typeof item?.msg === "string" ? item.msg : null)
      .filter(Boolean)
      .join(" ") || "Revisá los datos seleccionados.";
  }
  if (typeof detalle === "string") {
    return detalle;
  }

  return alternativo;
}

function ModalReprogramarTurno({
  turno,
  onCerrar,
  onTurnoReprogramado,
}: ModalReprogramarTurnoProps) {
  const [fecha, setFecha] = useState("");
  const [fechaHora, setFechaHora] = useState("");
  const [horarios, setHorarios] = useState<HorarioLibre[]>([]);
  const [consultando, setConsultando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");

  async function cargarHorarios(
    nuevaFecha: string,
    limpiarError = true,
  ) {
    setFecha(nuevaFecha);
    setFechaHora("");
    setHorarios([]);
    if (limpiarError) setError("");
    if (!nuevaFecha) return;

    setConsultando(true);
    try {
      setHorarios(await obtenerHorariosLibres(
        turno.prestacion_id,
        nuevaFecha,
        turno.id,
      ));
    } catch (err) {
      setError(obtenerMensajeError(
        err,
        "No se pudieron consultar los horarios libres.",
      ));
    } finally {
      setConsultando(false);
    }
  }

  async function guardar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setError("");
    setGuardando(true);

    try {
      onTurnoReprogramado(
        await reprogramarTurno(turno.id, fechaHora),
      );
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 409) {
        setError(
          "El horario dejó de estar disponible. Elegí otro horario.",
        );
        if (fecha) await cargarHorarios(fecha, false);
      } else {
        setError(obtenerMensajeError(
          err,
          "No se pudo reprogramar el turno.",
        ));
      }
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div className="modal-turno-fondo" role="presentation">
      <section
        className="modal-turno"
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-reprogramar-turno"
      >
        <header className="modal-turno-encabezado">
          <div>
            <p className="turnos-etiqueta">Agenda</p>
            <h2 id="titulo-reprogramar-turno">Reprogramar turno</h2>
          </div>
          <button type="button" onClick={onCerrar} aria-label="Cerrar">×</button>
        </header>

        <form className="formulario-turno" onSubmit={guardar}>
          <div className="formulario-turno-campos">
            <div className="reprogramar-turno-resumen">
              <p><span>Paciente</span><strong>{turno.paciente_nombre}</strong></p>
              <p><span>Profesional</span><strong>{turno.profesional_nombre}</strong></p>
              <p><span>Prestación</span><strong>{turno.prestacion_nombre}</strong></p>
              <p>
                <span>Turno actual</span>
                <strong>
                  {formatearFechaTurno(turno.fecha_hora)} · {formatearHoraTurno(turno.fecha_hora)} hs
                </strong>
              </p>
            </div>

            <label className="campo-observaciones">Nueva fecha
              <input
                type="date"
                min={fechaActualNegocio()}
                value={fecha}
                onChange={(evento) => void cargarHorarios(evento.target.value)}
                required
              />
            </label>

            <fieldset className="horarios-turno" disabled={!fecha || consultando}>
              <legend>Nuevo horario disponible</legend>
              {consultando && <p>Consultando horarios...</p>}
              {!consultando && fecha && horarios.length === 0 && (
                <p>No hay horarios disponibles para esta fecha.</p>
              )}
              {!consultando && horarios.map((horario) => (
                <label
                  key={horario.fecha_hora}
                  className={fechaHora === horario.fecha_hora ? "seleccionado" : ""}
                >
                  <input
                    type="radio"
                    name="nueva-fecha-hora"
                    value={horario.fecha_hora}
                    checked={fechaHora === horario.fecha_hora}
                    onChange={(evento) => setFechaHora(evento.target.value)}
                    required
                  />
                  {formatearHoraTurno(horario.fecha_hora)} hs
                </label>
              ))}
            </fieldset>
          </div>

          {error && <p className="mensaje-turnos-error" role="alert">{error}</p>}
          <footer className="formulario-turno-acciones">
            <button type="button" className="boton-cerrar-sesion" onClick={onCerrar}>
              Cancelar
            </button>
            <button type="submit" className="boton-primario" disabled={guardando || !fechaHora}>
              {guardando ? "Reprogramando..." : "Confirmar reprogramación"}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

export default ModalReprogramarTurno;
