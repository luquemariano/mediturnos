import { useEffect, useState } from "react";
import axios from "axios";
import { trackEvent } from "../analytics";
import { formatoFechaHoraPublica, formatoHoraPublica } from "../utils/publicDateTime";
import { obtenerDisponibilidadPublica } from "../services/publicBookingService";
import { obtenerReservaPublica, cancelarReservaPublica, reprogramarReservaPublica, type PublicReserva } from "../services/publicBookingService";
import "./PublicBooking.css";

export default function SelfService({ token }: { token: string }) {
  const [r, setR] = useState<PublicReserva | null>(null);
  const [errorCarga, setErrorCarga] = useState("");
  const [mensajeError, setMensajeError] = useState("");
  const [mensajeExito, setMensajeExito] = useState("");
  const [nuevaFecha, setNuevaFecha] = useState("");
  const [horarios, setHorarios] = useState<string[]>([]);
  const [horaSeleccionada, setHoraSeleccionada] = useState("");
  const [cargandoDisponibilidad, setCargandoDisponibilidad] = useState(false);
  const [mostrarReprogramacion, setMostrarReprogramacion] = useState(true);

  useEffect(() => {
    void obtenerReservaPublica(token).then(setR).catch(() => setErrorCarga("No encontramos esta reserva."));
  }, [token]);

  if (errorCarga) return <main className="public-booking"><h1>{errorCarga}</h1></main>;
  if (!r) return <main className="public-booking"><p>Cargando reserva…</p></main>;

  async function consultarDisponibilidad(fecha: string) {
    setNuevaFecha(fecha);
    setHoraSeleccionada("");
    if (!fecha || !r?.profesional_slug || !r.prestacion_identificador_publico) return;
    setCargandoDisponibilidad(true);
    try {
      const respuesta = await obtenerDisponibilidadPublica(r.profesional_slug, r.prestacion_identificador_publico, fecha);
      setHorarios(respuesta.dias[0]?.horarios ?? []);
    } catch {
      setHorarios([]);
    } finally {
      setCargandoDisponibilidad(false);
    }
  }

  async function cancelar() {
    if (!window.confirm("¿Querés cancelar este turno?")) return;
    setMensajeError("");
    setMensajeExito("");
    try {
      setR(await cancelarReservaPublica(token));
      setMensajeExito("Tu turno fue cancelado correctamente.");
      trackEvent("public_booking_cancel", { source: "self_service" });
    } catch {
      setMensajeError("No pudimos cancelar este turno.");
    }
  }

  async function reprogramar() {
    if (!horaSeleccionada) return;
    setMensajeError("");
    setMensajeExito("");
    try {
      const respuesta = await reprogramarReservaPublica(token, horaSeleccionada);
      setR(respuesta);
      setMensajeExito("Tu turno fue reprogramado correctamente.");
      setMensajeError("");
      setHoraSeleccionada("");
      setMostrarReprogramacion(false);
      trackEvent("public_booking_reschedule", { source: "self_service" });
    } catch (e) {
      const status = axios.isAxiosError(e) ? e.response?.status : undefined;
      setMensajeError(status === 409 ? "El horario seleccionado ya no está disponible." : status === 429 ? "Realizaste demasiados intentos. Probá nuevamente en unos minutos." : status === 400 ? "Elegí otro horario disponible." : "No pudimos reprogramar este turno.");
    }
  }

  return <main className="public-booking"><section className="public-card"><p className="public-kicker">Turnelia</p><h1>Tu reserva</h1><h2>{r.profesional.nombre} {r.profesional.apellido}</h2><p>{r.prestacion.nombre} · {r.prestacion.modalidad}</p><p>{formatoFechaHoraPublica(r.fecha_hora)}</p><strong>{r.estado}</strong>{mensajeExito && <div className="public-feedback public-feedback-success" role="status"><strong>{mensajeExito}</strong><span>Nueva fecha: {formatoFechaHoraPublica(r.fecha_hora)}.</span></div>}{mensajeError && <p className="public-feedback public-feedback-error" role="alert">{mensajeError}</p>}{["reservado", "confirmado"].includes(r.estado) && <>{mostrarReprogramacion ? <><label>Nueva fecha<input type="date" value={nuevaFecha} onChange={e => void consultarDisponibilidad(e.target.value)} /></label>{cargandoDisponibilidad ? <p>Cargando horarios disponibles…</p> : <fieldset><legend>Horarios disponibles</legend>{horarios.length ? horarios.map(h => <button type="button" key={h} disabled={h === r.fecha_hora} className={horaSeleccionada === h ? "selected" : ""} onClick={() => setHoraSeleccionada(h)}>{formatoHoraPublica(h)}</button>) : nuevaFecha && <p>No hay horarios disponibles para este día.</p>}</fieldset>}<div className="public-actions"><button type="button" onClick={reprogramar} disabled={!horaSeleccionada}>Reprogramar</button><button type="button" className="public-button-secondary" onClick={cancelar}>Cancelar turno</button></div></> : <div className="public-actions"><button type="button" className="public-button-secondary" onClick={() => { setMostrarReprogramacion(true); setMensajeExito(""); setNuevaFecha(""); setHorarios([]); }}>Volver a reprogramar</button><button type="button" className="public-button-secondary" onClick={cancelar}>Cancelar turno</button></div>}</>}</section></main>;
}
