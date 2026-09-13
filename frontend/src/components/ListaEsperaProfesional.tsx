import { useCallback, useEffect, useState } from "react";
import axios from "axios";
import ProfesionalShell from "./ProfesionalShell";
import type { PacienteSeleccion } from "../types/paciente";
import type { Prestacion } from "../types/prestacion";
import type { WaitlistEntry, WaitlistState } from "../types/waitlist";
import { obtenerPacientesParaProfesional } from "../services/pacienteService";
import { obtenerMisPrestaciones } from "../services/prestacionService";
import { cancelarWaitlist, crearWaitlist, listarWaitlist } from "../services/waitlistService";
import "./ListaEsperaProfesional.css";

type Props = { nombre: string; onVolver: () => void; onAbrirAgenda: () => void; onAbrirPacientes: () => void; onAbrirDisponibilidad: () => void; onAbrirPrestaciones: () => void; onAbrirPerfil: () => void; onCerrarSesion: () => void };
type Filter = "todas" | WaitlistState;
type Form = { paciente_id: string; prestacion_id: string; fecha_desde: string; fecha_hasta: string; hora_desde: string; hora_hasta: string };
const VACIO: Form = { paciente_id: "", prestacion_id: "", fecha_desde: "", fecha_hasta: "", hora_desde: "", hora_hasta: "" };
const estados: Array<{ value: Filter; label: string }> = [{ value: "todas", label: "Todos los estados" }, { value: "activa", label: "En espera" }, { value: "ofertada", label: "Turno ofrecido" }, { value: "reservada", label: "Reservada" }, { value: "cancelada", label: "Cancelada" }, { value: "vencida", label: "Vencida" }];

function detalle(error: unknown, fallback: string) { return axios.isAxiosError(error) && typeof error.response?.data?.detail === "string" ? error.response.data.detail : fallback; }
function fecha(value: string) { return new Intl.DateTimeFormat("es-AR", { dateStyle: "medium" }).format(new Date(`${value}T12:00:00`)); }
function fechaCreacion(value: string) { return new Intl.DateTimeFormat("es-AR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value)); }
function etiquetaEstado(value: WaitlistState) { return estados.find((item) => item.value === value)?.label ?? value; }

export default function ListaEsperaProfesional(props: Props) {
  const [items, setItems] = useState<WaitlistEntry[]>([]);
  const [pacientes, setPacientes] = useState<PacienteSeleccion[]>([]);
  const [prestaciones, setPrestaciones] = useState<Prestacion[]>([]);
  const [filtro, setFiltro] = useState<Filter>("todas");
  const [prestacionFiltro, setPrestacionFiltro] = useState("");
  const [form, setForm] = useState<Form>(VACIO);
  const [modal, setModal] = useState(false);
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [cancelando, setCancelando] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [exito, setExito] = useState("");

  const cargar = useCallback(async () => {
    setCargando(true); setError("");
    try {
      const [entradas, personas, servicios] = await Promise.all([
        listarWaitlist({ estado: filtro === "todas" ? undefined : filtro, prestacion_id: prestacionFiltro ? Number(prestacionFiltro) : undefined }),
        obtenerPacientesParaProfesional(),
        obtenerMisPrestaciones(),
      ]);
      setItems(entradas); setPacientes(personas); setPrestaciones(servicios);
    } catch (e) { setError(detalle(e, "No pudimos cargar tu lista de espera.")); }
    finally { setCargando(false); }
  }, [filtro, prestacionFiltro]);

  useEffect(() => { void cargar(); }, [cargar]);

  function abrirNueva() { setForm(VACIO); setError(""); setExito(""); setModal(true); }
  function cambiar<K extends keyof Form>(key: K, value: Form[K]) { setForm((actual) => ({ ...actual, [key]: value })); }
  function validar() {
    if (!form.paciente_id || !form.prestacion_id || !form.fecha_desde || !form.fecha_hasta) return "Completá paciente, prestación y rango de fechas.";
    if (form.fecha_hasta < form.fecha_desde) return "La fecha hasta no puede ser anterior a la fecha desde.";
    if (Boolean(form.hora_desde) !== Boolean(form.hora_hasta)) return "Indicá ambas horas o dejá el rango horario vacío.";
    if (form.hora_desde && form.hora_hasta <= form.hora_desde) return "La hora hasta debe ser posterior a la hora desde.";
    return "";
  }
  async function guardar(event: React.FormEvent) {
    event.preventDefault(); if (guardando) return;
    const validacion = validar(); if (validacion) { setError(validacion); return; }
    setGuardando(true); setError("");
    try {
      await crearWaitlist({ paciente_id: Number(form.paciente_id), prestacion_id: Number(form.prestacion_id), fecha_desde: form.fecha_desde, fecha_hasta: form.fecha_hasta, ...(form.hora_desde ? { hora_desde: form.hora_desde, hora_hasta: form.hora_hasta } : {}) });
      setModal(false); setExito("La entrada se agregó a la lista de espera."); await cargar();
    } catch (e) { setError(detalle(e, "No pudimos crear la entrada.")); }
    finally { setGuardando(false); }
  }
  async function cancelar(item: WaitlistEntry) {
    if (cancelando || !window.confirm(`¿Cancelar la espera de ${item.paciente_nombre}?`)) return;
    setCancelando(item.id); setError("");
    try { await cancelarWaitlist(item.id); setExito("La entrada fue cancelada."); await cargar(); }
    catch (e) { setError(detalle(e, "No pudimos cancelar la entrada.")); }
    finally { setCancelando(null); }
  }

  return <ProfesionalShell activo="lista-espera" nombre={props.nombre} tituloTopbar="Lista de espera" onAbrirInicio={props.onVolver} onAbrirAgenda={props.onAbrirAgenda} onAbrirPacientes={props.onAbrirPacientes} onAbrirDisponibilidad={props.onAbrirDisponibilidad} onAbrirPrestaciones={props.onAbrirPrestaciones} onAbrirPerfil={props.onAbrirPerfil} onCerrarSesion={props.onCerrarSesion}>
    <div className="waitlist-page">
      <header className="waitlist-header"><div><span className="waitlist-eyebrow">Continuidad de agenda</span><h1>Lista de espera</h1><p>Registrá preferencias y encontrá a quién avisar cuando se libera un horario.</p></div><button type="button" className="waitlist-primary" onClick={abrirNueva}>Agregar a la lista</button></header>
      {exito && <p className="waitlist-feedback success" role="status">{exito}</p>}{error && !modal && <p className="waitlist-feedback error" role="alert">{error}</p>}
      <section className="waitlist-toolbar" aria-label="Filtros de lista de espera"><label>Estado<select value={filtro} onChange={(e) => setFiltro(e.target.value as Filter)}>{estados.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label><label>Prestación<select value={prestacionFiltro} onChange={(e) => setPrestacionFiltro(e.target.value)}><option value="">Todas las prestaciones</option>{prestaciones.filter((item) => item.activa).map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select></label></section>
      {cargando ? <div className="waitlist-empty">Cargando tu lista de espera…</div> : items.length === 0 ? <section className="waitlist-empty"><div className="waitlist-empty-mark">↗</div><h2>No hay personas en esta vista</h2><p>Cuando alguien necesite otro horario, podés registrarlo acá y tenerlo listo para la próxima oportunidad.</p><button type="button" className="waitlist-secondary" onClick={abrirNueva}>Agregar primera entrada</button></section> : <div className="waitlist-list">{items.map((item) => <article className="waitlist-card" key={item.id}><div className="waitlist-card-main"><div className="waitlist-card-title"><h2>{item.paciente_nombre}</h2><span className={`waitlist-status status-${item.estado}`}>{etiquetaEstado(item.estado)}</span></div><p className="waitlist-service">{item.prestacion_nombre}</p><dl><div><dt>Rango de fechas</dt><dd>{fecha(item.fecha_desde)} – {fecha(item.fecha_hasta)}</dd></div><div><dt>Horario preferido</dt><dd>{item.hora_desde ? `${item.hora_desde.slice(0, 5)} – ${item.hora_hasta?.slice(0, 5)}` : "Cualquier horario"}</dd></div><div><dt>Agregada</dt><dd>{fechaCreacion(item.created_at)}</dd></div></dl></div>{item.estado === "ofertada" && <p className="waitlist-offer-note">Hay un turno ofrecido. La persona recibe los detalles por email.</p>}{item.estado === "activa" && <button type="button" className="waitlist-text-action" disabled={cancelando === item.id} onClick={() => void cancelar(item)}>{cancelando === item.id ? "Cancelando…" : "Cancelar espera"}</button>}</article>)}</div>}
    </div>
    {modal && <div className="waitlist-overlay" role="dialog" aria-modal="true" aria-labelledby="waitlist-modal-title"><form className="waitlist-modal" onSubmit={guardar}><header><div><span className="waitlist-eyebrow">Nueva preferencia</span><h2 id="waitlist-modal-title">Agregar a la lista</h2></div><button type="button" className="waitlist-close" aria-label="Cerrar" onClick={() => setModal(false)}>×</button></header><div className="waitlist-form"><label>Paciente *<select required value={form.paciente_id} onChange={(e) => cambiar("paciente_id", e.target.value)}><option value="">Elegí un paciente</option>{pacientes.map((item) => <option key={item.id} value={item.id}>{item.nombre} {item.apellido}</option>)}</select></label><label>Prestación *<select required value={form.prestacion_id} onChange={(e) => cambiar("prestacion_id", e.target.value)}><option value="">Elegí una prestación</option>{prestaciones.filter((item) => item.activa).map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select></label><div className="waitlist-form-grid"><label>Desde *<input required type="date" value={form.fecha_desde} onChange={(e) => cambiar("fecha_desde", e.target.value)} /></label><label>Hasta *<input required type="date" value={form.fecha_hasta} onChange={(e) => cambiar("fecha_hasta", e.target.value)} /></label><label>Hora desde<input type="time" value={form.hora_desde} onChange={(e) => cambiar("hora_desde", e.target.value)} /></label><label>Hora hasta<input type="time" value={form.hora_hasta} onChange={(e) => cambiar("hora_hasta", e.target.value)} /></label></div>{error && <p className="waitlist-feedback error" role="alert">{error}</p>}</div><footer><button type="button" className="waitlist-secondary" onClick={() => setModal(false)}>Cancelar</button><button type="submit" className="waitlist-primary" disabled={guardando}>{guardando ? "Guardando…" : "Agregar a la lista"}</button></footer></form></div>}
  </ProfesionalShell>;
}
