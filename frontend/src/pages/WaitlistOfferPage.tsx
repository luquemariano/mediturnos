import { useEffect, useState } from "react";
import axios from "axios";
import { aceptarOfertaWaitlist, obtenerOfertaWaitlist } from "../services/publicWaitlistService";
import type { PublicWaitlistOffer } from "../types/waitlist";
import "./WaitlistOfferPage.css";

type State = "loading" | "active" | "accepting" | "accepted" | "expired" | "unavailable" | "invalid";

function horario(value: string) {
  return new Intl.DateTimeFormat("es-AR", { dateStyle: "full", timeStyle: "short", timeZone: "America/Argentina/Buenos_Aires" }).format(new Date(value));
}
function vistaError(error: unknown): State {
  if (axios.isAxiosError(error) && error.response?.status === 409) return "unavailable";
  return "invalid";
}

export default function WaitlistOfferPage({ token }: { token: string }) {
  const [estado, setEstado] = useState<State>("loading");
  const [oferta, setOferta] = useState<PublicWaitlistOffer | null>(null);
  useEffect(() => { void obtenerOfertaWaitlist(token).then((item) => { setOferta(item); setEstado(item.estado === "activa" ? "active" : item.estado === "aceptada" ? "accepted" : "expired"); }).catch((error) => setEstado(vistaError(error))); }, [token]);
  async function aceptar() {
    if (!oferta || estado !== "active") return;
    setEstado("accepting");
    try { const actualizada = await aceptarOfertaWaitlist(token); setOferta(actualizada); setEstado(actualizada.estado === "aceptada" ? "accepted" : "unavailable"); }
    catch (error) { setEstado(vistaError(error)); }
  }
  if (estado === "loading") return <main className="offer-page"><section className="offer-card"><p>Cargando tu oferta…</p></section></main>;
  if (!oferta || estado === "invalid") return <main className="offer-page"><section className="offer-card"><span className="offer-kicker">Turnelia</span><h1>Esta oferta no está disponible</h1><p>El enlace no es válido o ya no podemos encontrar la oferta. Si necesitás ayuda, contactá al consultorio.</p></section></main>;
  if (estado === "expired") return <main className="offer-page"><section className="offer-card"><span className="offer-kicker">Turnelia · Lista de espera</span><h1>La oferta venció</h1><p>Este horario ya no puede aceptarse. Podés volver a consultar disponibilidad para buscar otra opción.</p><button type="button" className="offer-secondary" onClick={() => window.history.back()}>Volver</button></section></main>;
  if (estado === "unavailable") return <main className="offer-page"><section className="offer-card"><span className="offer-kicker">Turnelia · Lista de espera</span><h1>El horario ya no está disponible</h1><p>Otra persona pudo reservarlo antes de tu confirmación. La lista de espera seguirá buscando una alternativa compatible.</p><button type="button" className="offer-secondary" onClick={() => window.history.back()}>Volver</button></section></main>;
  return <main className="offer-page"><section className="offer-card"><span className="offer-kicker">Turnelia · Lista de espera</span><h1>{estado === "accepted" ? "Tu turno quedó reservado" : "Encontramos un horario para vos"}</h1><p>Hola {oferta.paciente}, el consultorio tiene una opción disponible.</p><dl className="offer-summary"><div><dt>Profesional</dt><dd>{oferta.profesional}</dd></div><div><dt>Prestación</dt><dd>{oferta.prestacion}</dd></div><div><dt>Horario</dt><dd>{horario(oferta.fecha_hora)}</dd></div></dl>{estado === "accepted" ? <div className="offer-confirmation" role="status">La reserva fue confirmada. Te enviaremos los detalles por email.</div> : <><p className="offer-expiry">Podés aceptar esta oferta hasta {horario(oferta.expires_at)}.</p><button type="button" className="offer-primary" disabled={estado === "accepting"} onClick={() => void aceptar()}>{estado === "accepting" ? "Confirmando…" : "Aceptar horario"}</button></>}</section></main>;
}
