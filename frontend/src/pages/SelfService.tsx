import { useEffect, useState } from "react";
import { trackEvent } from "../analytics";
import { obtenerReservaPublica, cancelarReservaPublica, reprogramarReservaPublica, type PublicReserva } from "../services/publicBookingService";
import "./PublicBooking.css";

export default function SelfService({ token }: { token: string }) {
  const [r, setR] = useState<PublicReserva | null>(null);
  const [error, setError] = useState("");
  const [nuevaFecha, setNuevaFecha] = useState("");

  useEffect(() => {
    void obtenerReservaPublica(token).then(setR).catch(() => setError("No encontramos esta reserva."));
  }, [token]);

  if (error) return <main className="public-booking"><h1>{error}</h1></main>;
  if (!r) return <main className="public-booking"><p>Cargando reserva…</p></main>;

  async function cancelar() {
    if (!window.confirm("¿Querés cancelar este turno?")) return;
    setR(await cancelarReservaPublica(token));
    trackEvent("public_booking_cancel", { source: "self_service" });
  }

  async function reprogramar() {
    if (!nuevaFecha) return;
    try {
      setR(await reprogramarReservaPublica(token, nuevaFecha));
      trackEvent("public_booking_reschedule", { source: "self_service" });
    } catch {
      setError("No pudimos reprogramar este turno.");
    }
  }

  return <main className="public-booking"><section className="public-card"><p className="public-kicker">Turnelia</p><h1>Tu reserva</h1><h2>{r.profesional.nombre} {r.profesional.apellido}</h2><p>{r.prestacion.nombre} · {r.prestacion.modalidad}</p><p>{new Date(r.fecha_hora).toLocaleString("es-AR", { dateStyle: "full", timeStyle: "short" })}</p><strong>{r.estado}</strong>{["reservado", "confirmado"].includes(r.estado) && <><label>Nueva fecha y hora<input type="datetime-local" value={nuevaFecha} onChange={e => setNuevaFecha(e.target.value)} /></label><button type="button" onClick={reprogramar}>Reprogramar</button><button type="button" onClick={cancelar}>Cancelar turno</button></>}</section></main>;
}
