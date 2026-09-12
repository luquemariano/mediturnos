import { useEffect, useMemo, useState } from "react";
import axios from "axios";

import "./AdopcionAdmin.css";
import { obtenerAdopcionAdmin } from "../services/adminAdoptionService";
import type { AdoptionStatus, AdminAdoptionItem } from "../types/adminAdoption";

const ESTADOS: Record<AdoptionStatus, string> = { sin_uso: "Sin uso", configurando: "Configurando", activo: "Activo", en_riesgo: "En riesgo", inactivo: "Inactivo" };
const ESTADOS_ORDEN: AdoptionStatus[] = ["activo", "en_riesgo", "inactivo", "configurando", "sin_uso"];
type Orden = "actividad" | "acceso" | "nombre" | "dias";

const fecha = (valor: string | null) => valor ? new Intl.DateTimeFormat("es-AR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(valor)) : "Nunca";
const fechaClave = (valor: string | null) => valor ? new Date(valor).getTime() : -Infinity;
const detalleError = (error: unknown) => axios.isAxiosError(error) && typeof error.response?.data?.detail === "string" ? error.response.data.detail : "No pudimos cargar las métricas de adopción.";

export default function AdopcionAdmin({ onVolver }: { onVolver: () => void }) {
  const [items, setItems] = useState<AdminAdoptionItem[]>([]);
  const [estado, setEstado] = useState<AdoptionStatus | "">("");
  const [q, setQ] = useState("");
  const [orden, setOrden] = useState<Orden>("actividad");
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [seleccionado, setSeleccionado] = useState<AdminAdoptionItem | null>(null);

  useEffect(() => {
    const controlador = new AbortController();
    const temporizador = window.setTimeout(() => {
      setCargando(true); setError("");
      void obtenerAdopcionAdmin({ status: estado || undefined, q: q.trim() || undefined }, controlador.signal)
        .then(setItems)
        .catch(errorActual => { if (!controlador.signal.aborted) setError(detalleError(errorActual)); })
        .finally(() => { if (!controlador.signal.aborted) setCargando(false); });
    }, 250);
    return () => { window.clearTimeout(temporizador); controlador.abort(); };
  }, [estado, q]);

  const ordenados = useMemo(() => [...items].sort((a, b) => {
    if (orden === "nombre") return `${a.apellido} ${a.nombre}`.localeCompare(`${b.apellido} ${b.nombre}`, "es");
    if (orden === "acceso") return fechaClave(b.last_login_at) - fechaClave(a.last_login_at);
    if (orden === "dias") return (b.days_since_last_activity ?? -1) - (a.days_since_last_activity ?? -1);
    return fechaClave(b.last_activity_at) - fechaClave(a.last_activity_at);
  }), [items, orden]);
  const resumen = useMemo(() => ESTADOS_ORDEN.reduce((acc, key) => ({ ...acc, [key]: items.filter(item => item.adoption_status === key).length }), {} as Record<AdoptionStatus, number>), [items]);

  return <main className="adopcion-admin-pagina"><section className="adopcion-admin-shell">
    <header className="adopcion-admin-header"><div><p>Administración global</p><h1>Adopción</h1><span>Entendé qué profesionales ya están usando Turnelia y dónde acompañarlos.</span></div><button type="button" onClick={onVolver}>Volver al panel</button></header>
    <section className="adopcion-resumen" aria-label="Resumen de adopción">{ESTADOS_ORDEN.map(key => <article className={`adopcion-metrica ${key}`} key={key}><span>{ESTADOS[key]}</span><strong>{cargando ? "—" : resumen[key]}</strong></article>)}</section>
    <section className="adopcion-herramientas" aria-label="Buscar y ordenar adopción"><label className="adopcion-busqueda">Buscar profesional<input aria-label="Buscar" value={q} onChange={e => setQ(e.target.value)} placeholder="Nombre, apellido o email" /></label><label>Estado<select aria-label="Estado" value={estado} onChange={e => setEstado(e.target.value as AdoptionStatus | "")}><option value="">Todos</option>{ESTADOS_ORDEN.map(key => <option value={key} key={key}>{ESTADOS[key]}</option>)}</select></label><label>Ordenar por<select aria-label="Ordenar por" value={orden} onChange={e => setOrden(e.target.value as Orden)}><option value="actividad">Última actividad</option><option value="acceso">Último acceso</option><option value="nombre">Nombre</option><option value="dias">Días sin actividad</option></select></label></section>
    <section className="adopcion-listado" aria-live="polite">
      {cargando && <div className="adopcion-estado" aria-label="Cargando adopción" aria-busy="true">Cargando métricas…</div>}
      {!cargando && error && <div className="adopcion-error" role="alert">{error}</div>}
      {!cargando && !error && ordenados.length === 0 && <div className="adopcion-estado"><h2>No encontramos profesionales</h2><p>Probá con otros términos o filtros.</p></div>}
      {!cargando && !error && ordenados.length > 0 && <div className="adopcion-tabla-contenedor"><table><thead><tr><th>Profesional</th><th>Email</th><th>Estado</th><th>Último acceso</th><th>Última actividad</th><th>Días sin actividad</th><th>Logins</th><th>Pacientes</th><th>Turnos</th><th>Prestaciones</th><th>Disponibilidades</th><th>Evoluciones</th></tr></thead><tbody>{ordenados.map(item => <tr key={item.profesional_id} onClick={() => setSeleccionado(item)}><td><button type="button" className="adopcion-profesional">{item.nombre} {item.apellido}</button></td><td>{item.email}</td><td><span className={`adopcion-badge ${item.adoption_status}`}>{ESTADOS[item.adoption_status]}</span></td><td>{fecha(item.last_login_at)}</td><td>{fecha(item.last_activity_at)}</td><td>{item.days_since_last_activity ?? "—"}</td><td>{item.login_count}</td><td>{item.patients_created}</td><td>{item.appointments_created}</td><td>{item.services_created}</td><td>{item.availabilities_created}</td><td>{item.clinical_evolutions_created}</td></tr>)}</tbody></table></div>}
    </section>
  </section>{seleccionado && <DetalleAdopcion item={seleccionado} onCerrar={() => setSeleccionado(null)} />}</main>;
}

function DetalleAdopcion({ item, onCerrar }: { item: AdminAdoptionItem; onCerrar: () => void }) {
  const datos: Array<[string, string | number]> = [["Primer acceso", fecha(item.first_login_at)], ["Último acceso", fecha(item.last_login_at)], ["Última actividad", fecha(item.last_activity_at)], ["Logins", item.login_count], ["Días activos", item.active_days], ["Pacientes creados", item.patients_created], ["Turnos creados", item.appointments_created], ["Prestaciones creadas", item.services_created], ["Disponibilidades creadas", item.availabilities_created], ["Evoluciones creadas", item.clinical_evolutions_created], ["Estado", ESTADOS[item.adoption_status]]];
  return <div className="adopcion-detalle-fondo" role="presentation" onMouseDown={e => { if (e.target === e.currentTarget) onCerrar(); }}><aside className="adopcion-detalle" role="dialog" aria-modal="true" aria-labelledby="adopcion-detalle-titulo"><header><div><p>Detalle de adopción</p><h2 id="adopcion-detalle-titulo">{item.nombre} {item.apellido}</h2><span>{item.email}</span></div><button type="button" aria-label="Cerrar detalle" onClick={onCerrar}>×</button></header><dl>{datos.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl></aside></div>;
}
