import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";

import "./CuentasAdmin.css";
import { activarSuscripcionAdmin, cambiarPlanAdmin, cancelarSuscripcionAdmin, extenderTrialAdmin, marcarPagoPendienteAdmin, obtenerCuentasAdmin, obtenerDetalleCuentaAdmin, obtenerHistorialCuentaAdmin, obtenerResumenCuentasAdmin, reactivarSuscripcionAdmin } from "../services/adminCuentaService";
import type { CuentaAdminDetalle, CuentaAdminItem, CuentasAdminPagina, CuentasAdminResumen, EstadoAdmin, EventoSuscripcionAdmin, PlanAdmin } from "../types/adminCuenta";

const LIMITE = 25;
const ESTADOS: Record<EstadoAdmin, string> = { trial: "Prueba gratuita", active: "Activo", past_due: "Pago pendiente", cancelled: "Cancelado", expired: "Prueba finalizada", sin_suscripcion: "Sin suscripción" };
const PLANES: Record<string, string> = { profesional: "Profesional", consultorio: "Consultorio", centro: "Centro" };
const fecha = (valor: string | null) => valor ? new Intl.DateTimeFormat("es-AR").format(new Date(valor)) : "—";
const detalleError = (error: unknown, fallback: string) => axios.isAxiosError(error) && typeof error.response?.data?.detail === "string" ? error.response.data.detail : fallback;

export default function CuentasAdmin({ onVolver }: { onVolver: () => void }) {
  const [resumen, setResumen] = useState<CuentasAdminResumen | null>(null);
  const [pagina, setPagina] = useState<CuentasAdminPagina | null>(null);
  const [q, setQ] = useState(""); const [estado, setEstado] = useState(""); const [plan, setPlan] = useState(""); const [periodo, setPeriodo] = useState(""); const [offset, setOffset] = useState(0);
  const [reintentoListado, setReintentoListado] = useState(0);
  const [cargandoResumen, setCargandoResumen] = useState(true); const [cargandoListado, setCargandoListado] = useState(true);
  const [errorResumen, setErrorResumen] = useState(""); const [errorListado, setErrorListado] = useState("");
  const [detalle, setDetalle] = useState<CuentaAdminDetalle | null>(null); const [detalleAbierto, setDetalleAbierto] = useState(false); const [cargandoDetalle, setCargandoDetalle] = useState(false); const [errorDetalle, setErrorDetalle] = useState("");

  const cargarResumen = useCallback(async () => { setCargandoResumen(true); setErrorResumen(""); try { setResumen(await obtenerResumenCuentasAdmin()); } catch { setErrorResumen("No pudimos cargar las métricas."); } finally { setCargandoResumen(false); } }, []);
  useEffect(() => { void cargarResumen(); }, [cargarResumen]);
  const createdFrom = useMemo(() => { if (!periodo) return undefined; const valor = new Date(); valor.setDate(valor.getDate() - Number(periodo)); return valor.toISOString().slice(0, 10); }, [periodo]);

  useEffect(() => {
    const controlador = new AbortController();
    const temporizador = window.setTimeout(() => {
      setCargandoListado(true); setErrorListado("");
      void obtenerCuentasAdmin({ q: q.trim() || undefined, estado: estado || undefined, plan: plan || undefined, created_from: createdFrom, offset, limit: LIMITE }, controlador.signal)
        .then(setPagina)
        .catch(error => { if (!controlador.signal.aborted) setErrorListado(detalleError(error, "No pudimos cargar las cuentas.")); })
        .finally(() => { if (!controlador.signal.aborted) setCargandoListado(false); });
    }, 350);
    return () => { window.clearTimeout(temporizador); controlador.abort(); };
  }, [createdFrom, estado, offset, plan, q, reintentoListado]);

  function actualizarFiltro(actualizar: () => void) { setOffset(0); actualizar(); }
  async function abrirDetalle(cuentaId: number) { setDetalleAbierto(true); setDetalle(null); setErrorDetalle(""); setCargandoDetalle(true); try { setDetalle(await obtenerDetalleCuentaAdmin(cuentaId)); } catch (error) { setErrorDetalle(detalleError(error, "No pudimos cargar el detalle.")); } finally { setCargandoDetalle(false); } }
  const paginaActual = Math.floor(offset / LIMITE) + 1; const paginas = Math.max(1, Math.ceil((pagina?.total ?? 0) / LIMITE));

  return <main className="cuentas-admin-pagina"><section className="cuentas-admin-shell">
    <header className="cuentas-admin-header"><div><p>Administración comercial</p><h1>Cuentas</h1><span>Consultá altas, planes y estado de suscripción.</span></div><button type="button" onClick={onVolver}>Volver al panel</button></header>
    <section className="cuentas-metricas" aria-label="Resumen comercial">
      {cargandoResumen && Array.from({ length: 5 }, (_, i) => <div key={i} className="cuenta-metrica skeleton" aria-hidden="true" />)}
      {!cargandoResumen && errorResumen && <div className="cuentas-error resumen" role="alert"><span>{errorResumen}</span><button type="button" onClick={() => void cargarResumen()}>Reintentar</button></div>}
      {!cargandoResumen && resumen && [
        ["Cuentas totales", resumen.cuentas_totales], ["En prueba gratuita", resumen.trials_activos], ["Activas", resumen.suscripciones_activas], ["Pruebas finalizadas", resumen.trials_finalizados], ["Altas últimos 30 días", resumen.altas_ultimos_30_dias],
      ].map(([etiqueta, valor]) => <article className="cuenta-metrica" key={etiqueta}><span>{etiqueta}</span><strong>{valor}</strong></article>)}
    </section>
    <section className="cuentas-herramientas" aria-label="Buscar y filtrar cuentas">
      <label className="cuentas-busqueda">Buscar<input value={q} onChange={e => actualizarFiltro(() => setQ(e.target.value))} placeholder="Cuenta, profesional, matrícula o email" /></label>
      <label>Estado<select value={estado} onChange={e => actualizarFiltro(() => setEstado(e.target.value))}><option value="">Todos</option><option value="trial">Prueba gratuita</option><option value="active">Activo</option><option value="past_due">Pago pendiente</option><option value="cancelled">Cancelado</option><option value="expired">Prueba finalizada</option></select></label>
      <label>Plan<select value={plan} onChange={e => actualizarFiltro(() => setPlan(e.target.value))}><option value="">Todos</option><option value="profesional">Profesional</option><option value="consultorio">Consultorio</option><option value="centro">Centro</option></select></label>
      <label>Alta<select value={periodo} onChange={e => actualizarFiltro(() => setPeriodo(e.target.value))}><option value="">Todas</option><option value="7">Últimos 7 días</option><option value="30">Últimos 30 días</option></select></label>
    </section>
    <section className="cuentas-listado" aria-live="polite">
      {cargandoListado && <div className="cuentas-cargando" aria-label="Cargando cuentas" aria-busy="true">Cargando cuentas…</div>}
      {!cargandoListado && errorListado && <div className="cuentas-error" role="alert"><span>{errorListado}</span><button type="button" onClick={() => setReintentoListado(valor => valor + 1)}>Reintentar</button></div>}
      {!cargandoListado && !errorListado && pagina?.items.length === 0 && <div className="cuentas-vacio"><h2>No encontramos cuentas</h2><p>Probá con otros términos o filtros.</p></div>}
      {!cargandoListado && !errorListado && pagina && pagina.items.length > 0 && <>
        <div className="cuentas-tabla-contenedor"><table><thead><tr><th>Cuenta</th><th>Profesional principal</th><th>Plan</th><th>Estado</th><th>Trial vence</th><th>Alta</th><th>Profesionales</th></tr></thead><tbody>{pagina.items.map(item => <FilaCuenta key={item.cuenta_id} item={item} onAbrir={abrirDetalle} />)}</tbody></table></div>
        <div className="cuentas-mobile-lista">{pagina.items.map(item => <TarjetaCuenta key={item.cuenta_id} item={item} onAbrir={abrirDetalle} />)}</div>
        <footer className="cuentas-paginacion"><span>Página {paginaActual} de {paginas} · {pagina.total} cuentas</span><div><button type="button" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - LIMITE))}>Anterior</button><button type="button" disabled={offset + LIMITE >= pagina.total} onClick={() => setOffset(offset + LIMITE)}>Siguiente</button></div></footer>
      </>}
    </section>
  </section>
  {detalleAbierto && <DetalleCuenta detalle={detalle} cargando={cargandoDetalle} error={errorDetalle} onActualizado={actualizado => { setDetalle(actualizado); setReintentoListado(valor => valor + 1); void cargarResumen(); }} onCerrar={() => { setDetalleAbierto(false); setDetalle(null); }} />}
  </main>;
}

function FilaCuenta({ item, onAbrir }: { item: CuentaAdminItem; onAbrir: (id: number) => void }) { const principal = item.profesional_principal; return <tr onClick={() => void onAbrir(item.cuenta_id)}><td><button type="button" className="cuenta-link">{item.nombre}</button><small>#{item.cuenta_id} · {item.tipo === "individual" ? "Individual" : "Organización"}</small></td><td>{principal ? <><strong>{principal.nombre} {principal.apellido}</strong><small>{principal.matricula}</small></> : <span className="dato-ausente">Sin profesional principal</span>}</td><td><Badge tipo="plan" valor={item.plan ? PLANES[item.plan] : "Sin plan"} /></td><td><Badge tipo={item.estado} valor={ESTADOS[item.estado]} /></td><td>{fecha(item.trial_ends_at)}</td><td>{fecha(item.created_at)}</td><td>{item.profesionales_count}</td></tr>; }
function TarjetaCuenta({ item, onAbrir }: { item: CuentaAdminItem; onAbrir: (id: number) => void }) { return <button type="button" className="cuenta-mobile-card" onClick={() => void onAbrir(item.cuenta_id)}><span><strong>{item.nombre}</strong><Badge tipo={item.estado} valor={ESTADOS[item.estado]} /></span><small>{item.profesional_principal ? `${item.profesional_principal.nombre} ${item.profesional_principal.apellido}` : "Sin profesional principal"}</small><small>{item.plan ? PLANES[item.plan] : "Sin plan"} · Trial vence {fecha(item.trial_ends_at)}</small><small>Alta {fecha(item.created_at)}</small></button>; }
function Badge({ tipo, valor }: { tipo: string; valor: string }) { return <span className={`cuenta-badge ${tipo}`}>{valor}</span>; }

function DetalleCuenta({ detalle, cargando, error, onCerrar, onActualizado }: { detalle: CuentaAdminDetalle | null; cargando: boolean; error: string; onCerrar: () => void; onActualizado: (detalle: CuentaAdminDetalle) => void }) {
  const [historial, setHistorial] = useState<EventoSuscripcionAdmin[]>([]); const [motivo, setMotivo] = useState(""); const [dias, setDias] = useState<7 | 14 | 30>(7); const [planNuevo, setPlanNuevo] = useState<PlanAdmin>("profesional"); const [accionando, setAccionando] = useState(""); const [mensaje, setMensaje] = useState("");
  const cuentaId = detalle?.cuenta.id;
  const cargarHistorial = useCallback(async () => { if (cuentaId) setHistorial(await obtenerHistorialCuentaAdmin(cuentaId)); }, [cuentaId]);
  useEffect(() => { if (cuentaId) void cargarHistorial().catch(() => setMensaje("No pudimos cargar el historial comercial.")); }, [cargarHistorial, cuentaId]);
  async function ejecutar(nombre: string, operacion: () => Promise<CuentaAdminDetalle>, confirmar = false) { if (confirmar && !window.confirm(`¿Confirmás la acción: ${nombre}?`)) return; setAccionando(nombre); setMensaje(""); try { const actualizado = await operacion(); onActualizado(actualizado); await cargarHistorial(); setMensaje("La acción comercial se guardó correctamente."); } catch (e) { setMensaje(detalleError(e, "No pudimos completar la acción comercial.")); } finally { setAccionando(""); } }
  const estado = detalle?.suscripcion?.estado;
  return <div className="cuenta-detalle-fondo" role="presentation" onMouseDown={e => { if (e.target === e.currentTarget) onCerrar(); }}><aside className="cuenta-detalle" role="dialog" aria-modal="true" aria-labelledby="cuenta-detalle-titulo"><header><div><p>Detalle comercial</p><h2 id="cuenta-detalle-titulo">{detalle?.cuenta.nombre ?? "Cuenta"}</h2></div><button type="button" aria-label="Cerrar detalle" onClick={onCerrar}>×</button></header>{cargando && <div className="detalle-cargando" aria-busy="true">Cargando detalle…</div>}{error && <p className="cuentas-error" role="alert">{error}</p>}{detalle && <div className="detalle-secciones">
    <Seccion titulo="Cuenta"><dl><Dato nombre="ID" valor={`#${detalle.cuenta.id}`} /><Dato nombre="Tipo" valor={detalle.cuenta.tipo === "individual" ? "Individual" : "Organización"} /><Dato nombre="Alta" valor={fecha(detalle.cuenta.created_at)} /><Dato nombre="Actualización" valor={fecha(detalle.cuenta.updated_at)} /></dl></Seccion>
    <Seccion titulo="Suscripción">{detalle.suscripcion ? <dl><Dato nombre="Plan" valor={PLANES[detalle.suscripcion.plan]} /><Dato nombre="Estado" valor={ESTADOS[detalle.suscripcion.estado]} /><Dato nombre="Trial iniciado" valor={fecha(detalle.suscripcion.trial_started_at)} /><Dato nombre="Trial vence" valor={fecha(detalle.suscripcion.trial_ends_at)} /><Dato nombre="Días restantes" valor={String(detalle.suscripcion.trial_days_remaining)} />{detalle.suscripcion.estado_persistido && <Dato nombre="Estado persistido" valor={ESTADOS[detalle.suscripcion.estado_persistido]} />}</dl> : <p className="dato-ausente">Esta cuenta no tiene suscripción asociada.</p>}</Seccion>
    {detalle.suscripcion && <Seccion titulo="Acciones comerciales"><div className="acciones-comerciales"><label>Motivo (opcional)<input value={motivo} maxLength={500} onChange={e => setMotivo(e.target.value)} placeholder="Ej. pago por transferencia" /></label><div className="acciones-fila">
      {(estado === "trial" || estado === "expired") && <button disabled={!!accionando} onClick={() => void ejecutar("Activar suscripción", () => activarSuscripcionAdmin(detalle.cuenta.id, motivo))}>Activar suscripción</button>}
      {(estado === "trial" || estado === "expired") && <><select aria-label="Días de extensión" value={dias} onChange={e => setDias(Number(e.target.value) as 7 | 14 | 30)}><option value={7}>+7 días</option><option value={14}>+14 días</option><option value={30}>+30 días</option></select><button disabled={!!accionando} onClick={() => void ejecutar("Extender prueba", () => extenderTrialAdmin(detalle.cuenta.id, dias, motivo))}>Extender prueba</button></>}
      {(estado === "past_due" || estado === "cancelled") && <button disabled={!!accionando} onClick={() => void ejecutar("Reactivar", () => reactivarSuscripcionAdmin(detalle.cuenta.id, motivo), true)}>Reactivar</button>}
      {estado === "active" && <button disabled={!!accionando} onClick={() => void ejecutar("Marcar pago pendiente", () => marcarPagoPendienteAdmin(detalle.cuenta.id, motivo), true)}>Marcar pago pendiente</button>}
      {estado !== "cancelled" && <button className="peligro" disabled={!!accionando} onClick={() => void ejecutar("Cancelar", () => cancelarSuscripcionAdmin(detalle.cuenta.id, motivo), true)}>Cancelar</button>}
    </div><div className="acciones-plan"><select aria-label="Nuevo plan" value={planNuevo} onChange={e => setPlanNuevo(e.target.value as PlanAdmin)}><option value="profesional">Profesional</option><option value="consultorio">Consultorio</option><option value="centro">Centro</option></select><button disabled={!!accionando || planNuevo === detalle.suscripcion.plan} onClick={() => void ejecutar("Cambiar plan", () => cambiarPlanAdmin(detalle.cuenta.id, planNuevo, motivo))}>Cambiar plan</button></div>{accionando && <p role="status">Guardando {accionando.toLowerCase()}…</p>}{mensaje && <p role="status">{mensaje}</p>}</div></Seccion>}
    <Seccion titulo="Historial comercial">{historial.length ? <ol className="historial-comercial">{historial.map(e => <li key={e.id}><time>{new Intl.DateTimeFormat("es-AR", { dateStyle: "short", timeStyle: "short" }).format(new Date(e.created_at))}</time><strong>{e.actor_nombre ?? "Sistema"}</strong><span>{e.plan_anterior !== e.plan_nuevo && e.plan_nuevo ? `${PLANES[e.plan_anterior ?? ""] ?? "—"} → ${PLANES[e.plan_nuevo]}` : `${e.estado_anterior ? ESTADOS[e.estado_anterior] : "—"} → ${e.estado_nuevo ? ESTADOS[e.estado_nuevo] : "—"}`}</span>{e.motivo && <small>{e.motivo}</small>}</li>)}</ol> : <p className="dato-ausente">Todavía no hay eventos comerciales.</p>}</Seccion>
    <Seccion titulo={`Miembros (${detalle.miembros.length})`}>{detalle.miembros.length ? <ul>{detalle.miembros.map(item => <li key={item.usuario_id}><div><strong>{item.nombre}</strong><span>{item.email}</span></div><small>{item.rol_cuenta} · {item.activo ? "Activo" : "Inactivo"}</small></li>)}</ul> : <p className="dato-ausente">Sin miembros asociados.</p>}</Seccion>
    <Seccion titulo={`Profesionales (${detalle.profesionales.length})`}>{detalle.profesionales.length ? <ul>{detalle.profesionales.map(item => <li key={item.id}><div><strong>{item.nombre} {item.apellido}</strong><span>{item.email ?? "Sin email"}</span></div><small>{item.matricula} · {item.activo ? "Activo" : "Inactivo"}</small></li>)}</ul> : <p className="dato-ausente">Sin profesionales asociados.</p>}</Seccion>
  </div>}</aside></div>;
}
function Seccion({ titulo, children }: { titulo: string; children: React.ReactNode }) { return <section><h3>{titulo}</h3>{children}</section>; }
function Dato({ nombre, valor }: { nombre: string; valor: string }) { return <div><dt>{nombre}</dt><dd>{valor}</dd></div>; }
