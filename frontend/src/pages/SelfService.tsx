import { useEffect, useState } from "react";
import axios from "axios";
import { trackEvent } from "../analytics";
import { obtenerDisponibilidadPublica } from "../services/publicBookingService";
import { obtenerReservaPublica, cancelarReservaPublica, reprogramarReservaPublica, type PublicReserva } from "../services/publicBookingService";
import "./PublicBooking.css";

export default function SelfService({ token }: { token: string }) {
  const [r, setR] = useState<PublicReserva | null>(null);
  const [error, setError] = useState("");
  const [nuevaFecha, setNuevaFecha] = useState("");
  const [horarios, setHorarios] = useState<string[]>([]);
  const [horaSeleccionada, setHoraSeleccionada] = useState("");
  const [cargandoDisponibilidad, setCargandoDisponibilidad] = useState(false);

  useEffect(() => {
    void obtenerReservaPublica(token).then(setR).catch(() => setError("No encontramos esta reserva."));
  }, [token]);

  if (error) return <main className="public-booking"><h1>{error}</h1></main>;
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
    setR(await cancelarReservaPublica(token));
    trackEvent("public_booking_cancel", { source: "self_service" });
  }

  async function reprogramar() {
    if (!nuevaFecha) return;
    try {
      setR(await reprogramarReservaPublica(token, horaSeleccionada));
      trackEvent("public_booking_reschedule", { source: "self_service" });
    } catch (e) {
      const status = axios.isAxiosError(e) ? e.response?.status : undefined;
      setError(status === 409 ? "El horario seleccionado ya no está disponible." : status === 429 ? "Realizaste demasiados intentos. Probá nuevamente en unos minutos." : status === 400 ? "Elegí otro horario disponible." : "No pudimos reprogramar este turno.");
    }
  }

  return <main className="public-booking"><section className="public-card"><p className="public-kicker">Turnelia</p><h1>Tu reserva</h1><h2>{r.profesional.nombre} {r.profesional.apellido}</h2><p>{r.prestacion.nombre} · {r.prestacion.modalidad}</p><p>{new Date(r.fecha_hora).toLocaleString("es-AR", { dateStyle: "full", timeStyle: "short" })}</p><strong>{r.estado}</strong>{["reservado", "confirmado"].includes(r.estado) && <><label>Nueva fecha<input type="date" value={nuevaFecha} onChange={e => void consultarDisponibilidad(e.target.value)} /></label>{cargandoDisponibilidad ? <p>Cargando horarios disponibles…</p> : <fieldset><legend>Horarios disponibles</legend>{horarios.length ? horarios.map(h => <button type="button" key={h} className={horaSeleccionada === h ? "selected" : ""} onClick={() => setHoraSeleccionada(h)}>{new Date(h).toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" })}</button>) : nuevaFecha && <p>No hay horarios disponibles para este día.</p>}</fieldset>}<button type="button" onClick={reprogramar} disabled={!horaSeleccionada}>Reprogramar</button><button type="button" onClick={cancelar}>Cancelar turno</button></>}</section></main>;
}
