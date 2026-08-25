import { useEffect, useState } from "react";
import axios from "axios";

import "./RetornoSuscripcion.css";
import { obtenerCuentaActual } from "../services/cuentaService";
import { sincronizarSuscripcion } from "../services/suscripcionService";
import type { EstadoSuscripcionSaas } from "../types/suscripcion";

function fechaLarga(valor: string | null): string {
  if (!valor) return "la fecha configurada en tu cuenta";
  return new Intl.DateTimeFormat("es-AR", { dateStyle: "long" }).format(new Date(valor));
}

function errorSeguro(error: unknown): string {
  const status = axios.isAxiosError(error) ? error.response?.status : undefined;
  if (status === 502 || status === 503) {
    return "No pudimos verificar la suscripción con Mercado Pago. Podés volver a Turnelia e intentar sincronizarla nuevamente.";
  }
  return "No pudimos verificar el estado de la suscripción. Intentá nuevamente desde Turnelia.";
}

function mensajeEstado(suscripcion: EstadoSuscripcionSaas): { titulo: string; detalle: string } {
  if (suscripcion.estado === "trial") {
    return {
      titulo: "Tu medio de pago quedó asociado.",
      detalle: `Tu período de prueba continúa hasta ${fechaLarga(suscripcion.trial_ends_at)}. Todavía no se realizó ningún cobro.`,
    };
  }
  if (suscripcion.estado === "active") {
    return { titulo: "Tu suscripción está activa.", detalle: "La suscripción quedó sincronizada correctamente." };
  }
  if (suscripcion.estado === "past_due") {
    return { titulo: "Hay un inconveniente con tu suscripción.", detalle: "Revisá el medio de pago desde Turnelia." };
  }
  if (suscripcion.estado === "cancelled") {
    return { titulo: "Tu suscripción está cancelada.", detalle: "Podés consultar los planes disponibles desde Turnelia." };
  }
  return { titulo: "Tu suscripción está vencida.", detalle: "Podés consultar los planes disponibles desde Turnelia." };
}

export default function RetornoSuscripcion({
  autenticada,
  onIngresar,
  onVolver,
}: {
  autenticada: boolean;
  onIngresar: () => void;
  onVolver: () => void;
}) {
  const [cargando, setCargando] = useState(autenticada);
  const [resultado, setResultado] = useState<EstadoSuscripcionSaas | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!autenticada) {
      setCargando(false);
      return;
    }
    let activo = true;
    void obtenerCuentaActual()
      .then((cuenta) => sincronizarSuscripcion(cuenta.cuenta_id))
      .then((respuesta) => { if (activo) setResultado(respuesta.suscripcion); })
      .catch((fallo) => { if (activo) setError(errorSeguro(fallo)); })
      .finally(() => { if (activo) setCargando(false); });
    return () => { activo = false; };
  }, [autenticada]);

  return <main className="retorno-suscripcion">
    <section className="retorno-panel" aria-live="polite">
      <p className="retorno-kicker">Suscripción Turnelia</p>
      <h1>{cargando ? "Verificando tu suscripción…" : resultado ? mensajeEstado(resultado).titulo : autenticada ? "No pudimos verificar tu suscripción" : "Ingresá para verificar tu suscripción"}</h1>
      {cargando && <p>Estamos consultando el estado con Turnelia.</p>}
      {!autenticada && !cargando && <p>El retorno no utiliza datos de la URL. Iniciá sesión para consultar el estado real de tu cuenta.</p>}
      {resultado && <p>{mensajeEstado(resultado).detalle}</p>}
      {error && <p role="alert" className="retorno-error">{error}</p>}
      <div className="retorno-acciones">
        {!autenticada && <button type="button" onClick={onIngresar}>Ingresar</button>}
        <button type="button" className="retorno-secundario" onClick={onVolver}>Volver a Turnelia</button>
      </div>
    </section>
  </main>;
}
