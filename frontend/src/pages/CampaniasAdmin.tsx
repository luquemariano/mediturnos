import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import api from "../api/api";

type Novedad = { id: number; titulo: string; descripcion_corta: string; prioridad: "normal" | "importante"; cerrada: boolean; activa: boolean };
type Destinatario = { id: number; nombre: string; email: string };

export default function CampaniasAdmin({ onVolver }: { onVolver: () => void }) {
  const [novedades, setNovedades] = useState<Novedad[]>([]);
  const [destinatarios, setDestinatarios] = useState<Destinatario[]>([]);
  const [totalDestinatarios, setTotalDestinatarios] = useState(0);
  const [busqueda, setBusqueda] = useState("");
  const [seleccion, setSeleccion] = useState<number[]>([]);
  const [todos, setTodos] = useState(true);
  const [asunto, setAsunto] = useState("");
  const [preheader, setPreheader] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [novedadesElegidas, setNovedadesElegidas] = useState<number[]>([]);
  const [preview, setPreview] = useState<{ asunto: string; html: string; texto: string; destinatarios: number } | null>(null);
  const [estado, setEstado] = useState("");
  const [enviada, setEnviada] = useState(false);
  const [edicion, setEdicion] = useState<Novedad | null>(null);
  const [idempotencyKey] = useState(() => globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`);

  const cargar = useCallback(async () => {
    const [n, d, todosLosDestinatarios] = await Promise.all([api.get<Novedad[]>("/admin/campanias/novedades"), api.get<Destinatario[]>("/admin/campanias/destinatarios", { params: busqueda ? { busqueda } : {} }), api.get<Destinatario[]>("/admin/campanias/destinatarios")]);
    setNovedades(n.data); setDestinatarios(d.data); setTotalDestinatarios(todosLosDestinatarios.data.length);
  }, [busqueda]);
  useEffect(() => { void cargar(); }, [cargar]);
  const cantidadSeleccionada = todos ? totalDestinatarios : seleccion.length;
  const payload = useMemo(() => ({ asunto, preheader, mensaje_principal: mensaje, novedades_ids: novedadesElegidas, todos, destinatarios_ids: todos ? [] : seleccion, idempotency_key: idempotencyKey }), [asunto, preheader, mensaje, novedadesElegidas, todos, seleccion, idempotencyKey]);

  async function guardarNovedad(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!edicion) return;
    if (edicion.id) await api.put(`/admin/campanias/novedades/${edicion.id}`, edicion); else await api.post("/admin/campanias/novedades", edicion);
    setEdicion(null); await cargar();
  }
  async function previsualizar() {
    const response = await api.post("/admin/campanias/preview", payload); setPreview(response.data);
  }
  async function enviar() {
    if (!window.confirm(`Vas a enviar “${asunto}” a ${cantidadSeleccionada} profesionales. El envío comienza inmediatamente. ¿Confirmás?`)) return;
    const creado = await api.post("/admin/campanias", payload);
    const resultado = await api.post(`/admin/campanias/${creado.data.id}/enviar`, { confirmar: true });
    setEstado(`Campaña enviada: ${resultado.data.enviadas} entregas correctas y ${resultado.data.fallidas} fallidas.`);
    setEnviada(true);
  }
  const cerradasActivas = novedades.filter((n) => n.cerrada && n.activa);

  return <main className="pagina-dashboard"><section className="dashboard" style={{ maxWidth: 1000 }}>
    <header className="dashboard-encabezado"><div><p className="dashboard-etiqueta">Administración global</p><h1>Campañas de novedades</h1></div><button className="boton-secundario" onClick={onVolver}>Volver</button></header>
    {estado && <p role="status">{estado}</p>}
    <section className="tarjeta-login"><h2>1. Novedades para incluir</h2><p>Elegí novedades activas y cerradas para esta campaña.</p>{cerradasActivas.length ? cerradasActivas.map((n) => <label key={n.id} style={{ display: "block", padding: 8 }}><input type="checkbox" checked={novedadesElegidas.includes(n.id)} onChange={(e) => setNovedadesElegidas((v) => e.target.checked ? [...v, n.id] : v.filter((id) => id !== n.id))} /> {n.titulo} — {n.descripcion_corta} {n.prioridad === "importante" ? "· Importante" : ""}</label>) : <p>No hay novedades cerradas activas.</p>}</section>
    <section className="tarjeta-login"><h2>2. Contenido del email</h2><label>Asunto<input value={asunto} onChange={(e) => setAsunto(e.target.value)} /></label><label>Preheader<input value={preheader} onChange={(e) => setPreheader(e.target.value)} /></label><label>Mensaje principal<textarea rows={5} value={mensaje} onChange={(e) => setMensaje(e.target.value)} /></label></section>
    <section className="tarjeta-login"><h2>3. Destinatarios</h2><label><input type="radio" checked={todos} onChange={() => setTodos(true)} /> Todos los profesionales activos excepto quienes se dieron de baja</label><label><input type="radio" checked={!todos} onChange={() => setTodos(false)} /> Selección manual</label>{!todos && <><label>Buscar profesional<input value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Nombre o email" /></label><div style={{ maxHeight: 200, overflow: "auto" }}>{destinatarios.map((d) => <label key={d.id} style={{ display: "block" }}><input type="checkbox" checked={seleccion.includes(d.id)} onChange={(e) => setSeleccion((v) => e.target.checked ? [...v, d.id] : v.filter((id) => id !== d.id))} /> {d.nombre} · {d.email}</label>)}</div></>}<p><strong>{cantidadSeleccionada}</strong> destinatarios</p></section>
    <section className="tarjeta-login"><h2>4. Vista previa y envío</h2><button type="button" className="boton-secundario" onClick={() => void previsualizar()} disabled={!asunto || !preheader || !mensaje}>Vista previa del email</button>{preview && <><p>Asunto: {preview.asunto} · Para {preview.destinatarios} destinatarios</p><iframe title="Vista previa del email" sandbox="" srcDoc={preview.html} style={{ width: "100%", minHeight: 500, border: "1px solid #d9e0dc", background: "#f6f5f0" }} /><details><summary>Versión de texto</summary><pre>{preview.texto}</pre></details></>}<button type="button" onClick={() => void enviar()} disabled={enviada || !preview || !asunto || !preheader || !mensaje || cantidadSeleccionada === 0}>{enviada ? "Envío completado" : "Enviar ahora"}</button></section>
    <section className="tarjeta-login"><h2>Gestión de novedades</h2><button type="button" className="boton-secundario" onClick={() => setEdicion({ id: 0, titulo: "", descripcion_corta: "", prioridad: "normal", cerrada: false, activa: true })}>Crear novedad</button>{novedades.map((n) => <p key={n.id}>{n.titulo} · {n.cerrada ? "Cerrada" : "En curso"} · {n.activa ? "Activa" : "Inactiva"} <button type="button" onClick={() => setEdicion(n)}>Editar</button></p>)}</section>
    {edicion && <div role="dialog" aria-modal="true" className="tarjeta-login"><form onSubmit={(e) => void guardarNovedad(e)}><h2>{edicion.id ? "Editar" : "Crear"} novedad</h2><label>Título<input required value={edicion.titulo} onChange={(e) => setEdicion({ ...edicion, titulo: e.target.value })} /></label><label>Descripción corta<input required value={edicion.descripcion_corta} onChange={(e) => setEdicion({ ...edicion, descripcion_corta: e.target.value })} /></label><label>Prioridad<select value={edicion.prioridad} onChange={(e) => setEdicion({ ...edicion, prioridad: e.target.value as Novedad["prioridad"] })}><option value="normal">Normal</option><option value="importante">Importante</option></select></label><label><input type="checkbox" checked={edicion.cerrada} onChange={(e) => setEdicion({ ...edicion, cerrada: e.target.checked })} /> Cerrada</label><label><input type="checkbox" checked={edicion.activa} onChange={(e) => setEdicion({ ...edicion, activa: e.target.checked })} /> Activa</label><button type="submit">Guardar</button><button type="button" className="boton-secundario" onClick={() => setEdicion(null)}>Cancelar</button></form></div>}
  </section></main>;
}
