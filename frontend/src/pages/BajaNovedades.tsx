import { useState } from "react";
import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL?.trim() ?? "http://127.0.0.1:8000";
export default function BajaNovedades({ token }: { token: string | null }) {
  const [estado, setEstado] = useState<"confirmar" | "invalido" | "hecho">(token ? "confirmar" : "invalido");
  async function confirmar() {
    if (!token) return;
    try { await axios.post(`${baseURL}/public/baja-novedades`, { token }); setEstado("hecho"); }
    catch { setEstado("invalido"); }
  }
  return <main className="pagina-login"><section className="tarjeta-login"><p className="dashboard-etiqueta">Turnelia</p>{estado === "confirmar" && <><h1>Darse de baja</h1><p>Confirmá si querés dejar de recibir novedades de Turnelia en este correo.</p><button onClick={() => void confirmar()}>Confirmar baja</button></>}{estado === "hecho" && <><h1>Baja confirmada</h1><p>Ya no recibirás novedades de Turnelia en este correo.</p></>}{estado === "invalido" && <><h1>Enlace inválido o vencido</h1><p>Solicitá un nuevo enlace desde un email reciente de Turnelia.</p></>}</section></main>;
}
