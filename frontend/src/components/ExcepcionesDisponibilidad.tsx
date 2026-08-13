import { useCallback, useEffect, useMemo, useState } from "react";
/* eslint-disable no-unused-expressions */
import type { FormEvent } from "react";
import axios from "axios";

import "./ExcepcionesDisponibilidad.css";
import { cerrarMiDisponibilidadPorRango, crearMiExcepcion, eliminarMiExcepcion, obtenerMisExcepciones, reabrirMiDisponibilidadPorRango } from "../services/disponibilidadService";
import type { DisponibilidadExcepcion, TipoDisponibilidadExcepcion } from "../types/disponibilidad";
import { fechaActualNegocio } from "../utils/fechaTurno";

function mensajeError(error: unknown, alternativo: string) {
  if (!axios.isAxiosError(error)) return alternativo;
  return typeof error.response?.data?.detail === "string" ? error.response.data.detail : alternativo;
}

function fechaLegible(fecha: string) {
  const texto = new Intl.DateTimeFormat("es-AR", { weekday: "long", day: "numeric", month: "long" }).format(new Date(`${fecha}T12:00:00`));
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

function diasEntre(desde: string, hasta: string) {
  if (!desde || !hasta) return 0;
  return Math.floor((new Date(`${hasta}T12:00:00`).getTime() - new Date(`${desde}T12:00:00`).getTime()) / 86400000) + 1;
}

type GrupoCierres = { tipo: "grupo_cierres"; fecha_desde: string; fecha_hasta: string; items: DisponibilidadExcepcion[] };

function agruparExcepciones(items: DisponibilidadExcepcion[]): Array<DisponibilidadExcepcion | GrupoCierres> {
  const cierres = items.filter((item) => item.tipo === "cierre_dia").sort((a, b) => a.fecha.localeCompare(b.fecha));
  const grupos: GrupoCierres[] = [];
  for (const cierre of cierres) {
    const ultimo = grupos.at(-1);
    const siguiente = ultimo && diasEntre(ultimo.fecha_hasta, cierre.fecha) === 2;
    if (ultimo && siguiente) { ultimo.fecha_hasta = cierre.fecha; ultimo.items.push(cierre); }
    else grupos.push({ tipo: "grupo_cierres", fecha_desde: cierre.fecha, fecha_hasta: cierre.fecha, items: [cierre] });
  }
  return [...grupos, ...items.filter((item) => item.tipo === "franja_extraordinaria")]
    .sort((a, b) => ("fecha" in a ? a.fecha : a.fecha_desde).localeCompare("fecha" in b ? b.fecha : b.fecha_desde));
}

export default function ExcepcionesDisponibilidad() {
  const [items, setItems] = useState<DisponibilidadExcepcion[]>([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState("");
  const [modo, setModo] = useState<TipoDisponibilidadExcepcion | null>(null);
  const [fecha, setFecha] = useState("");
  const [inicio, setInicio] = useState("");
  const [fin, setFin] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");
  const [exito, setExito] = useState("");
  const [eliminando, setEliminando] = useState<DisponibilidadExcepcion | null>(null);
  const [vacacionesAbiertas, setVacacionesAbiertas] = useState(false);
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [grupoReabrir, setGrupoReabrir] = useState<GrupoCierres | null>(null);

  const cargar = useCallback(async () => {
    setCargando(true); setErrorCarga("");
    try { setItems(await obtenerMisExcepciones(fechaActualNegocio())); }
    catch (e) { setErrorCarga(mensajeError(e, "No pudimos cargar las excepciones.")); }
    finally { setCargando(false); }
  }, []);
  useEffect(() => { void cargar(); }, [cargar]);
  const ordenadas = useMemo(() => [...items].sort((a, b) => a.fecha.localeCompare(b.fecha) || (a.hora_inicio ?? "").localeCompare(b.hora_inicio ?? "")), [items]);
  const visuales = useMemo(() => agruparExcepciones(ordenadas), [ordenadas]);
  const cantidadDias = diasEntre(desde, hasta);

  function abrir(nuevoModo: TipoDisponibilidadExcepcion) {
    setModo(nuevoModo); setFecha(""); setInicio(""); setFin(""); setError(""); setExito("");
  }

  async function guardar(evento: FormEvent) {
    evento.preventDefault();
    if (!modo || guardando) return;
    if (!fecha) { setError("Seleccioná una fecha."); return; }
    if (modo === "franja_extraordinaria" && (!inicio || !fin || fin <= inicio)) {
      setError("La hora de finalización debe ser posterior a la de inicio."); return;
    }
    setGuardando(true); setError("");
    try {
      const creada = await crearMiExcepcion({ tipo: modo, fecha, ...(modo === "franja_extraordinaria" ? { hora_inicio: inicio, hora_fin: fin } : {}) });
      setItems((actuales) => [...actuales, creada]);
      setModo(null);
      setExito(modo === "cierre_dia" ? "Día cerrado correctamente." : "Horario especial agregado correctamente.");
    } catch (e) { setError(mensajeError(e, "No pudimos guardar la excepción.")); }
    finally { setGuardando(false); }
  }

  async function confirmarEliminar() {
    if (!eliminando || guardando) return;
    setGuardando(true); setError("");
    try {
      await eliminarMiExcepcion(eliminando.id);
      setItems((actuales) => actuales.filter((item) => item.id !== eliminando.id));
      setExito(eliminando.tipo === "cierre_dia" ? "Fecha reabierta correctamente." : "Horario especial eliminado correctamente.");
      setEliminando(null);
    } catch (e) { setError(mensajeError(e, "No pudimos eliminar la excepción.")); }
    finally { setGuardando(false); }
  }

  async function guardarVacaciones(evento: FormEvent) {
    evento.preventDefault();
    if (guardando) return;
    if (!desde || !hasta) { setError("Completá ambas fechas."); return; }
    if (cantidadDias < 1) { setError("La fecha hasta debe ser igual o posterior a la fecha desde."); return; }
    if (cantidadDias > 365) { setError("El período no puede superar los 365 días."); return; }
    setGuardando(true); setError("");
    try {
      const resultado = await cerrarMiDisponibilidadPorRango({ fecha_desde: desde, fecha_hasta: hasta });
      await cargar();
      setVacacionesAbiertas(false);
      setExito(resultado.ya_existentes ? `Se cerraron ${resultado.creados} días. ${resultado.ya_existentes} ya estaban cerrados.` : "Período cerrado correctamente.");
    } catch (e) { setError(mensajeError(e, "No pudimos cerrar el período.")); }
    finally { setGuardando(false); }
  }

  async function confirmarReabrirGrupo() {
    if (!grupoReabrir || guardando) return;
    setGuardando(true); setError("");
    try {
      await reabrirMiDisponibilidadPorRango({ fecha_desde: grupoReabrir.fecha_desde, fecha_hasta: grupoReabrir.fecha_hasta });
      setItems((actuales) => actuales.filter((item) => item.tipo !== "cierre_dia" || item.fecha < grupoReabrir.fecha_desde || item.fecha > grupoReabrir.fecha_hasta));
      setGrupoReabrir(null); setExito("Período reabierto correctamente.");
    } catch (e) { setError(mensajeError(e, "No pudimos reabrir el período.")); }
    finally { setGuardando(false); }
  }

  return <section className="mi-excepciones" aria-labelledby="mi-excepciones-titulo">
    <header><div><span>Excepciones por fecha</span><h2 id="mi-excepciones-titulo">Cambios puntuales</h2><p>Usá excepciones para cerrar un día puntual o abrir un horario especial sin modificar tu semana habitual.</p></div><div className="mi-excepciones-acciones"><button type="button" onClick={() => abrir("cierre_dia")}>Cerrar un día</button><button type="button" onClick={() => { setVacacionesAbiertas(true); setDesde(""); setHasta(""); setError(""); setExito(""); }}>Cargar vacaciones</button><button type="button" onClick={() => abrir("franja_extraordinaria")}>Agregar horario especial</button></div></header>
    {exito && <p role="status" className="mi-excepciones-feedback exito">{exito}</p>}
    {cargando ? <div className="mi-excepciones-cargando" aria-label="Cargando excepciones"><span /><span /></div>
      : errorCarga ? <div className="mi-excepciones-vacio" role="alert"><p>{errorCarga}</p><button type="button" onClick={() => void cargar()}>Reintentar</button></div>
      : ordenadas.length === 0 ? <div className="mi-excepciones-vacio"><strong>Sin cambios próximos</strong><p>Tu semana habitual se aplicará sin excepciones.</p></div>
      : <ol>{visuales.map((item) => "fecha" in item ? <li key={`e-${item.id}`}><i className={item.tipo} aria-hidden="true" /><div><strong>{fechaLegible(item.fecha)}</strong><small>Horario especial</small></div><time>{item.hora_inicio?.slice(0, 5)}–{item.hora_fin?.slice(0, 5)}</time><button type="button" onClick={() => { setEliminando(item); setError(""); }}>Eliminar horario</button></li> : <li key={`g-${item.fecha_desde}`} className="mi-excepciones-periodo"><i className="cierre_dia" aria-hidden="true" /><div><strong>{item.fecha_desde === item.fecha_hasta ? fechaLegible(item.fecha_desde) : `${fechaLegible(item.fecha_desde)} — ${fechaLegible(item.fecha_hasta)}`}</strong><small>{item.items.length === 1 ? "Día cerrado" : `Período cerrado · ${item.items.length} días`}</small></div><button type="button" onClick={() => { item.items.length === 1 ? setEliminando(item.items[0]) : setGrupoReabrir(item); setError(""); }}>{item.items.length === 1 ? "Reabrir fecha" : "Reabrir período"}</button></li>)}</ol>}

    {vacacionesAbiertas && <div className="mi-excepciones-modal-fondo"><section role="dialog" aria-modal="true" aria-labelledby="mi-excepciones-vacaciones-titulo" className="mi-excepciones-modal"><span>Cierre por período</span><h3 id="mi-excepciones-vacaciones-titulo">Cargar vacaciones</h3><form onSubmit={guardarVacaciones}><div className="mi-disp-horas"><label>Desde<input aria-label="Fecha desde" type="date" min={fechaActualNegocio()} value={desde} disabled={guardando} onChange={(e) => setDesde(e.target.value)} /></label><label>Hasta<input aria-label="Fecha hasta" type="date" min={desde || fechaActualNegocio()} value={hasta} disabled={guardando} onChange={(e) => setHasta(e.target.value)} /></label></div>{cantidadDias > 0 && <p className="mi-excepciones-dia">Se cerrarán {cantidadDias} días para nuevas reservas.</p>}<p className="mi-excepciones-aviso"><strong>Los turnos ya creados dentro del período no serán cancelados.</strong></p>{error && <p role="alert" className="mi-excepciones-feedback error">{error}</p>}<div className="mi-excepciones-modal-acciones"><button type="button" disabled={guardando} onClick={() => setVacacionesAbiertas(false)}>Volver</button><button type="submit" disabled={guardando}>{guardando ? "Guardando…" : "Confirmar"}</button></div></form></section></div>}

    {grupoReabrir && <div className="mi-excepciones-modal-fondo"><section role="dialog" aria-modal="true" aria-labelledby="mi-excepciones-reabrir-periodo" className="mi-excepciones-modal"><span>Período cerrado</span><h3 id="mi-excepciones-reabrir-periodo">Reabrir período</h3><p className="mi-excepciones-resumen"><strong>{fechaLegible(grupoReabrir.fecha_desde)} — {fechaLegible(grupoReabrir.fecha_hasta)}</strong></p><p>Este período volverá a usar tu disponibilidad habitual. Los horarios especiales existentes no se modificarán.</p>{error && <p role="alert" className="mi-excepciones-feedback error">{error}</p>}<div className="mi-excepciones-modal-acciones"><button type="button" disabled={guardando} onClick={() => setGrupoReabrir(null)}>Volver</button><button type="button" disabled={guardando} onClick={() => void confirmarReabrirGrupo()}>{guardando ? "Guardando…" : "Reabrir período"}</button></div></section></div>}

    {modo && <div className="mi-excepciones-modal-fondo"><section role="dialog" aria-modal="true" aria-labelledby="mi-excepciones-modal-titulo" className="mi-excepciones-modal"><span>{modo === "cierre_dia" ? "Cierre puntual" : "Horario extraordinario"}</span><h3 id="mi-excepciones-modal-titulo">{modo === "cierre_dia" ? "Cerrar un día" : "Agregar horario especial"}</h3><form onSubmit={guardar}><label>Fecha<input aria-label="Fecha" type="date" min={fechaActualNegocio()} value={fecha} disabled={guardando} onChange={(e) => setFecha(e.target.value)} /></label>{fecha && <p className="mi-excepciones-dia">{fechaLegible(fecha)}</p>}{modo === "franja_extraordinaria" && <div className="mi-disp-horas"><label>Desde<input aria-label="Desde" type="time" value={inicio} disabled={guardando} onChange={(e) => setInicio(e.target.value)} /></label><label>Hasta<input aria-label="Hasta" type="time" value={fin} disabled={guardando} onChange={(e) => setFin(e.target.value)} /></label></div>}<p className="mi-excepciones-aviso">{modo === "cierre_dia" ? "Ese día dejará de ofrecer horarios para nuevas reservas. " : "Este horario se ofrecerá sólo en la fecha seleccionada. "}<strong>Los turnos ya creados no serán cancelados.</strong></p>{error && <p role="alert" className="mi-excepciones-feedback error">{error}</p>}<div className="mi-excepciones-modal-acciones"><button type="button" disabled={guardando} onClick={() => setModo(null)}>Volver</button><button type="submit" disabled={guardando}>{guardando ? "Guardando…" : "Confirmar"}</button></div></form></section></div>}

    {eliminando && <div className="mi-excepciones-modal-fondo"><section role="dialog" aria-modal="true" aria-labelledby="mi-excepciones-eliminar-titulo" className="mi-excepciones-modal"><span>Excepción por fecha</span><h3 id="mi-excepciones-eliminar-titulo">{eliminando.tipo === "cierre_dia" ? "Reabrir esta fecha" : "Eliminar horario especial"}</h3><p className="mi-excepciones-resumen"><strong>{fechaLegible(eliminando.fecha)}</strong>{eliminando.tipo === "franja_extraordinaria" && <><br />{eliminando.hora_inicio?.slice(0, 5)}–{eliminando.hora_fin?.slice(0, 5)}</>}</p><p>Este cambio sólo afecta los próximos horarios disponibles. Los turnos existentes permanecen sin cambios.</p>{error && <p role="alert" className="mi-excepciones-feedback error">{error}</p>}<div className="mi-excepciones-modal-acciones"><button type="button" disabled={guardando} onClick={() => setEliminando(null)}>Volver</button><button type="button" className="eliminar" disabled={guardando} onClick={() => void confirmarEliminar()}>{guardando ? "Guardando…" : eliminando.tipo === "cierre_dia" ? "Reabrir fecha" : "Eliminar horario"}</button></div></section></div>}
  </section>;
}
