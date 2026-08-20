import { useEffect, useRef, useState } from "react";
import axios from "axios";

import "./ActivarSuscripcion.css";
import { obtenerCuentaActual } from "../services/cuentaService";
import {
  iniciarSuscripcion,
  obtenerSuscripcion,
} from "../services/suscripcionService";
import { montarFormularioMercadoPago } from "../services/mercadoPagoCardForm";
import type { CuentaActual, PlanCode } from "../types/cuenta";
import type { EstadoSuscripcionSaas } from "../types/suscripcion";

const PLANES: Array<{ code: PlanCode; nombre: string; precio: number }> = [
  { code: "profesional", nombre: "Profesional", precio: 34_900 },
  { code: "consultorio", nombre: "Consultorio", precio: 69_900 },
  { code: "centro", nombre: "Centro", precio: 149_900 },
];

function fechaArgentina(valor: string | null): string {
  if (!valor) return "Sin fecha disponible";
  return new Intl.DateTimeFormat("es-AR", { dateStyle: "long" }).format(
    new Date(valor),
  );
}

function mensajeError(error: unknown): string {
  const status = axios.isAxiosError(error) ? error.response?.status : undefined;
  if (status === 409) return "Ya existe una suscripción o un intento de alta pendiente.";
  if (status === 502) return "Mercado Pago no pudo procesar la solicitud. Podés reintentar de forma segura.";
  if (status === 503) return "La integración o el plan todavía no están configurados.";
  return "No pudimos asociar el medio de pago.";
}

export default function ActivarSuscripcion({ onVolver }: { onVolver: () => void }) {
  const [cuenta, setCuenta] = useState<CuentaActual | null>(null);
  const [suscripcion, setSuscripcion] = useState<EstadoSuscripcionSaas | null>(null);
  const [plan, setPlan] = useState<PlanCode>("profesional");
  const [procesando, setProcesando] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");
  const [tokenDebug, setTokenDebug] = useState("");
  const procesandoRef = useRef(false);
  const elegido = PLANES.find((item) => item.code === plan) ?? PLANES[0];

  useEffect(() => {
    let activo = true;
    void obtenerCuentaActual().then(async (actual) => {
      const estado = await obtenerSuscripcion(actual.cuenta_id);
      if (activo) {
        setCuenta(actual);
        setSuscripcion(estado);
        setPlan(actual.plan);
      }
    }).catch(() => activo && setError("No pudimos consultar la suscripción."));
    return () => { activo = false; };
  }, []);

  useEffect(() => {
    if (!cuenta) return;
    let desmontar: (() => void) | undefined;
    let activo = true;
    void montarFormularioMercadoPago({
      amount: elegido.precio,
      onToken: async (cardTokenId) => {
        const modoDiagnostico = !import.meta.env.PROD
          && import.meta.env.VITE_MERCADOPAGO_DEBUG_CARD_TOKEN === "true";
        if (modoDiagnostico) {
          setTokenDebug(cardTokenId);
          setError("");
          setMensaje("");
          return;
        }
        if (procesandoRef.current) return;
        procesandoRef.current = true;
        setProcesando(true);
        setError("");
        setMensaje("");
        try {
          const respuesta = await iniciarSuscripcion(cuenta.cuenta_id, plan, cardTokenId);
          setMensaje(respuesta.estado === "trial"
            ? "El medio de pago quedó asociado. Tu cuenta continúa en período de prueba y todavía no se realizó ningún cobro."
            : "El medio de pago quedó asociado correctamente.");
          setSuscripcion((actual) => actual ? { ...actual, plan, estado: respuesta.estado } : actual);
        } catch (fallo) {
          setError(mensajeError(fallo));
        } finally {
          procesandoRef.current = false;
          setProcesando(false);
        }
      },
      onError: () => setError("Revisá los datos del medio de pago."),
    }).then((limpiar) => { if (activo) desmontar = limpiar; else limpiar(); })
      .catch(() => activo && setError("No se pudo iniciar el formulario seguro de Mercado Pago."));
    return () => { activo = false; desmontar?.(); };
  }, [cuenta, elegido.precio, plan]);

  return <main className="suscripcion-pagina">
    <section className="suscripcion-panel">
      <button type="button" className="suscripcion-volver" onClick={onVolver}>← Volver</button>
      <header><p>Facturación y suscripción</p><h1>Activar un plan Turnelia</h1></header>
      {suscripcion && <div className="suscripcion-trial">
        <strong>Estado actual: {suscripcion.estado === "trial" ? "Período de prueba" : suscripcion.estado}</strong>
        <span>Finaliza el {fechaArgentina(suscripcion.trial_ends_at)}</span>
      </div>}

      <fieldset className="suscripcion-planes" disabled={procesando}>
        <legend>Elegí tu plan</legend>
        {PLANES.map((item) => <label key={item.code} className={plan === item.code ? "seleccionado" : ""}>
          <input type="radio" name="plan" value={item.code} checked={plan === item.code}
            onChange={() => setPlan(item.code)} />
          <strong>{item.nombre}</strong><span>${item.precio.toLocaleString("es-AR")}/mes</span>
        </label>)}
      </fieldset>

      <p className="suscripcion-aviso">Plan seleccionado: <strong>{elegido.nombre}</strong>. El primer cobro se programará al finalizar el período de prueba.</p>

      <form id="form-checkout" className="suscripcion-tarjeta">
        <h2>Medio de pago</h2>
        <label>Número de tarjeta<div id="form-checkout__cardNumber" className="campo-seguro" /></label>
        <div className="suscripcion-fila">
          <label>Vencimiento<div id="form-checkout__expirationDate" className="campo-seguro" /></label>
          <label>Código de seguridad<div id="form-checkout__securityCode" className="campo-seguro" /></label>
        </div>
        <label>Titular<input id="form-checkout__cardholderName" type="text" autoComplete="cc-name" /></label>
        <label>Email del titular<input id="form-checkout__cardholderEmail" type="email" /></label>
        <label>Tipo de documento<select id="form-checkout__identificationType" /></label>
        <label>Número de documento<input id="form-checkout__identificationNumber" type="text" /></label>
        <select id="form-checkout__issuer" hidden aria-label="Emisor" />
        <select id="form-checkout__installments" hidden aria-label="Cuotas" />
        <button id="form-checkout__submit" type="submit" disabled={procesando || !cuenta}>
          {procesando ? "Procesando…" : "Asociar medio de pago"}
        </button>
      </form>
      {tokenDebug && <output className="suscripcion-token-debug" aria-label="Card token de diagnóstico">
        {tokenDebug}
      </output>}
      {mensaje && <p role="status" className="suscripcion-exito">{mensaje}</p>}
      {error && <p role="alert" className="suscripcion-error">{error}</p>}
    </section>
  </main>;
}
