import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import api from "../api/api";
import "./CampaniasAdmin.css";

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
  const [errorGuardarNovedad, setErrorGuardarNovedad] = useState("");
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
    const payloadNovedad = {
      titulo: edicion.titulo,
      descripcion_corta: edicion.descripcion_corta,
      prioridad: edicion.prioridad,
      cerrada: edicion.cerrada,
      activa: edicion.activa,
    };
    setErrorGuardarNovedad("");
    try {
      if (edicion.id) await api.put(`/admin/campanias/novedades/${edicion.id}`, payloadNovedad);
      else await api.post("/admin/campanias/novedades", payloadNovedad);
    } catch {
      setErrorGuardarNovedad("No pudimos guardar la novedad. Intentá nuevamente.");
      return;
    }
    setErrorGuardarNovedad("");
    setEdicion(null);
    await cargar();
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

  return <main className="pagina-dashboard campanias-admin-pagina">
    <section className="campanias-admin">
      <header className="campanias-admin__header">
        <div>
          <p className="campanias-admin__eyebrow">Administración global</p>
          <h1>Campañas de novedades</h1>
          <p className="campanias-admin__intro">Prepará una actualización para profesionales y revisá el email antes de enviarlo.</p>
        </div>
        <button type="button" className="campanias-button campanias-button--quiet" onClick={onVolver}>Volver al panel</button>
      </header>

      {estado && <p className="campanias-status" role="status">{estado}</p>}

      <div className="campanias-workflow">
        <section className="campanias-card" aria-labelledby="campanias-novedades-titulo">
          <header className="campanias-card__header">
            <span className="campanias-step" aria-hidden="true">1</span>
            <div><h2 id="campanias-novedades-titulo">Novedades para incluir</h2><p>Elegí las novedades activas que ya estén cerradas.</p></div>
          </header>
          {cerradasActivas.length ? <div className="campanias-checklist">
            {cerradasActivas.map((n) => <label className="campanias-check-row" key={n.id}>
              <input type="checkbox" checked={novedadesElegidas.includes(n.id)} onChange={(e) => setNovedadesElegidas((v) => e.target.checked ? [...v, n.id] : v.filter((id) => id !== n.id))} />
              <span><strong>{n.titulo}</strong><small>{n.descripcion_corta}</small></span>
              {n.prioridad === "importante" && <span className="campanias-priority">Importante</span>}
            </label>)}
          </div> : <p className="campanias-empty">No hay novedades cerradas activas.</p>}
        </section>

        <section className="campanias-card" aria-labelledby="campanias-contenido-titulo">
          <header className="campanias-card__header">
            <span className="campanias-step" aria-hidden="true">2</span>
            <div><h2 id="campanias-contenido-titulo">Contenido del email</h2><p>Definí el asunto y el mensaje que recibirán los profesionales.</p></div>
          </header>
          <div className="campanias-form-fields">
            <label htmlFor="campanias-asunto">Asunto<input id="campanias-asunto" value={asunto} onChange={(e) => setAsunto(e.target.value)} /></label>
            <label htmlFor="campanias-preheader">Preheader<input id="campanias-preheader" value={preheader} onChange={(e) => setPreheader(e.target.value)} /></label>
            <label htmlFor="campanias-mensaje">Mensaje principal<textarea id="campanias-mensaje" rows={5} value={mensaje} onChange={(e) => setMensaje(e.target.value)} /></label>
          </div>
        </section>

        <section className="campanias-card" aria-labelledby="campanias-destinatarios-titulo">
          <header className="campanias-card__header">
            <span className="campanias-step" aria-hidden="true">3</span>
            <div><h2 id="campanias-destinatarios-titulo">Destinatarios</h2><p>Elegí a quiénes querés enviar esta campaña.</p></div>
          </header>
          <fieldset className="campanias-recipient-options">
            <legend className="campanias-sr-only">Modo de selección de destinatarios</legend>
            <label><input type="radio" name="modo-destinatarios" checked={todos} onChange={() => setTodos(true)} /><span><strong>Todos los profesionales activos</strong><small>Se excluyen quienes se dieron de baja.</small></span></label>
            <label><input type="radio" name="modo-destinatarios" checked={!todos} onChange={() => setTodos(false)} /><span><strong>Selección manual</strong><small>Elegí profesionales de la lista.</small></span></label>
          </fieldset>
          {!todos && <div className="campanias-manual-selection">
            <label htmlFor="campanias-busqueda">Buscar profesional<input id="campanias-busqueda" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Nombre o email" /></label>
            <div className="campanias-recipient-list" role="group" aria-label="Profesionales disponibles">
              {destinatarios.map((d) => <label className="campanias-recipient-row" key={d.id}>
                <input type="checkbox" checked={seleccion.includes(d.id)} onChange={(e) => setSeleccion((v) => e.target.checked ? [...v, d.id] : v.filter((id) => id !== d.id))} />
                <span><strong>{d.nombre}</strong><small>{d.email}</small></span>
              </label>)}
              {destinatarios.length === 0 && <p className="campanias-empty">No encontramos profesionales con esa búsqueda.</p>}
            </div>
          </div>}
          <p className="campanias-recipient-count" aria-live="polite"><strong>{cantidadSeleccionada}</strong><span>{cantidadSeleccionada === 1 ? "destinatario" : "destinatarios"}</span></p>
        </section>

        <section className="campanias-card campanias-card--preview" aria-labelledby="campanias-preview-titulo">
          <header className="campanias-card__header">
            <span className="campanias-step" aria-hidden="true">4</span>
            <div><h2 id="campanias-preview-titulo">Vista previa y envío</h2><p>Revisá el mensaje completo. El envío comienza al confirmar “Enviar ahora”.</p></div>
          </header>
          <div className="campanias-preview-actions">
            <button type="button" className="campanias-button campanias-button--secondary" onClick={() => void previsualizar()} disabled={!asunto || !preheader || !mensaje}>Vista previa del email</button>
            {preview && <span className="campanias-preview-note">Vista previa para {preview.destinatarios} {preview.destinatarios === 1 ? "destinatario" : "destinatarios"}</span>}
          </div>
          {preview && <div className="campanias-preview-content">
            <p className="campanias-preview-subject"><span>Asunto</span><strong>{preview.asunto}</strong></p>
            <iframe title="Vista previa del email" sandbox="" srcDoc={preview.html} />
            <details><summary>Ver versión de texto</summary><pre>{preview.texto}</pre></details>
          </div>}
          <footer className="campanias-send-footer">
            <p>Se enviará inmediatamente a <strong>{cantidadSeleccionada}</strong> {cantidadSeleccionada === 1 ? "profesional" : "profesionales"}.</p>
            <button type="button" className="campanias-button campanias-button--primary" onClick={() => void enviar()} disabled={enviada || !preview || !asunto || !preheader || !mensaje || cantidadSeleccionada === 0}>{enviada ? "Envío completado" : "Enviar ahora"}</button>
          </footer>
        </section>
      </div>

      <section className="campanias-management" aria-labelledby="campanias-gestion-titulo">
        <header><div><p className="campanias-admin__eyebrow">Catálogo</p><h2 id="campanias-gestion-titulo">Gestión de novedades</h2><p>Administrá las novedades que aparecerán en futuras campañas.</p></div>
          <button type="button" className="campanias-button campanias-button--secondary" onClick={() => { setErrorGuardarNovedad(""); setEdicion({ id: 0, titulo: "", descripcion_corta: "", prioridad: "normal", cerrada: false, activa: true }); }}>Crear novedad</button>
        </header>
        {novedades.length > 0 ? <ul className="campanias-news-list">{novedades.map((n) => <li key={n.id}>
          <div><strong>{n.titulo}</strong><p>{n.descripcion_corta}</p></div>
          <div className="campanias-news-meta"><span className={n.cerrada ? "is-closed" : ""}>{n.cerrada ? "Cerrada" : "En curso"}</span><span className={n.activa ? "is-active" : ""}>{n.activa ? "Activa" : "Inactiva"}</span></div>
          <button type="button" className="campanias-button campanias-button--quiet" onClick={() => { setErrorGuardarNovedad(""); setEdicion(n); }}>Editar</button>
        </li>)}</ul> : <p className="campanias-empty">Todavía no hay novedades en el catálogo.</p>}
      </section>

      {edicion && <div className="campanias-dialog-backdrop">
        <section role="dialog" aria-modal="true" aria-labelledby="campanias-dialog-titulo" className="campanias-dialog">
          <form onSubmit={(e) => void guardarNovedad(e)}>
            <header><p className="campanias-admin__eyebrow">Catálogo de novedades</p><h2 id="campanias-dialog-titulo">{edicion.id ? "Editar novedad" : "Crear novedad"}</h2></header>
            <div className="campanias-form-fields">
              <label htmlFor="novedad-titulo">Título<input id="novedad-titulo" required value={edicion.titulo} onChange={(e) => setEdicion({ ...edicion, titulo: e.target.value })} /></label>
              <label htmlFor="novedad-descripcion">Descripción corta<input id="novedad-descripcion" required value={edicion.descripcion_corta} onChange={(e) => setEdicion({ ...edicion, descripcion_corta: e.target.value })} /></label>
              <label htmlFor="novedad-prioridad">Prioridad<select id="novedad-prioridad" value={edicion.prioridad} onChange={(e) => setEdicion({ ...edicion, prioridad: e.target.value as Novedad["prioridad"] })}><option value="normal">Normal</option><option value="importante">Importante</option></select></label>
            </div>
            <div className="campanias-toggle-list">
              <label><input type="checkbox" checked={edicion.cerrada} onChange={(e) => setEdicion({ ...edicion, cerrada: e.target.checked })} /> Cerrada</label>
              <label><input type="checkbox" checked={edicion.activa} onChange={(e) => setEdicion({ ...edicion, activa: e.target.checked })} /> Activa</label>
            </div>
            {errorGuardarNovedad && <p className="campanias-status" role="alert">{errorGuardarNovedad}</p>}
            <footer><button type="button" className="campanias-button campanias-button--quiet" onClick={() => { setErrorGuardarNovedad(""); setEdicion(null); }}>Cancelar</button><button type="submit" className="campanias-button campanias-button--primary">Guardar novedad</button></footer>
          </form>
        </section>
      </div>}
    </section>
  </main>;
}
