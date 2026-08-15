import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";

import ProfesionalShell from "./ProfesionalShell";
import Icono from "./Icono";
import "./Pacientes.css";
import type { EvolucionClinica, PacienteSeleccion } from "../types/paciente";
import {
  buscarPacientesProfesional,
  crearPacienteProfesional,
  desactivarPacienteProfesional,
  editarPacienteProfesional,
  obtenerHistorialPaciente,
  obtenerEvolucionesPaciente,
  crearEvolucionPaciente,
} from "../services/pacienteService";

type Props = {
  nombre: string;
  onVolver: () => void;
  onAbrirAgenda: () => void;
  onAbrirDisponibilidad: () => void;
  onAbrirPrestaciones: () => void;
  onAbrirPerfil: () => void;
  onCerrarSesion: () => void;
};

type Historial = Awaited<ReturnType<typeof obtenerHistorialPaciente>>[number];
const FORM_VACIO = { nombre: "", apellido: "", dni: "", telefono: "", email: "", fecha_nacimiento: "" };
const ZONA_HORARIA = "America/Argentina/Buenos_Aires";

function detalleError(error: unknown): string {
  return axios.isAxiosError(error) && typeof error.response?.data?.detail === "string"
    ? error.response.data.detail : "Ocurrió un error inesperado.";
}

function etiquetaEstado(estado: string): string {
  return estado === "reservado" ? "Pendiente" : estado.charAt(0).toUpperCase() + estado.slice(1);
}

function fechaHistorial(fecha: string): string {
  return new Intl.DateTimeFormat("es-AR", {
    timeZone: ZONA_HORARIA, weekday: "short", day: "2-digit", month: "short",
    year: "numeric", hour: "2-digit", minute: "2-digit",
  }).format(new Date(fecha));
}

export default function Pacientes(props: Props) {
  const [pacientes, setPacientes] = useState<PacienteSeleccion[]>([]);
  const [q, setQ] = useState("");
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [form, setForm] = useState(FORM_VACIO);
  const [modal, setModal] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [seleccion, setSeleccion] = useState<PacienteSeleccion | null>(null);
  const [editando, setEditando] = useState(false);
  const [historial, setHistorial] = useState<Historial[]>([]);
  const [cargandoHistorial, setCargandoHistorial] = useState(false);
  const [confirmar, setConfirmar] = useState(false);
  const [evoluciones, setEvoluciones] = useState<EvolucionClinica[]>([]);
  const [cargandoEvoluciones, setCargandoEvoluciones] = useState(false);
  const [formEvolucion, setFormEvolucion] = useState(false);
  const [contenidoEvolucion, setContenidoEvolucion] = useState("");
  const [guardandoEvolucion, setGuardandoEvolucion] = useState(false);
  const [errorEvolucion, setErrorEvolucion] = useState("");

  const cargar = useCallback(async (termino = "") => {
    setCargando(true); setError("");
    try { setPacientes(await buscarPacientesProfesional(termino)); }
    catch (e) { setError(detalleError(e)); }
    finally { setCargando(false); }
  }, []);

  useEffect(() => {
    const temporizador = setTimeout(() => void cargar(q), 250);
    return () => clearTimeout(temporizador);
  }, [q, cargar]);

  async function guardar(evento: FormEvent) {
    evento.preventDefault();
    if (guardando) return;
    setGuardando(true); setError("");
    try {
      const datos = Object.fromEntries(Object.entries(form).map(([clave, valor]) => [clave, valor || null]));
      if (editando && seleccion) {
        const paciente = await editarPacienteProfesional(seleccion.id, datos);
        setSeleccion(paciente); setMensaje("Paciente actualizado correctamente.");
      } else {
        await crearPacienteProfesional(datos as Omit<PacienteSeleccion, "id">);
        setMensaje("Paciente creado correctamente.");
      }
      setModal(false); setEditando(false); setForm(FORM_VACIO);
      await cargar(q);
    } catch (e) { setError(detalleError(e)); }
    finally { setGuardando(false); }
  }

  async function ver(paciente: PacienteSeleccion) {
    setSeleccion(paciente); setConfirmar(false); setHistorial([]); setEvoluciones([]); setFormEvolucion(false); setContenidoEvolucion(""); setErrorEvolucion(""); setCargandoHistorial(true); setCargandoEvoluciones(true);
    try {
      const [turnos, registros] = await Promise.all([obtenerHistorialPaciente(paciente.id), obtenerEvolucionesPaciente(paciente.id)]);
      setHistorial(turnos); setEvoluciones(registros);
    }
    catch (e) { setError(detalleError(e)); }
    finally { setCargandoHistorial(false); setCargandoEvoluciones(false); }
  }

  async function guardarEvolucion(evento: FormEvent) {
    evento.preventDefault();
    if (!seleccion || guardandoEvolucion || !contenidoEvolucion.trim()) return;
    setGuardandoEvolucion(true); setErrorEvolucion("");
    try {
      const nueva = await crearEvolucionPaciente(seleccion.id, contenidoEvolucion);
      setEvoluciones((actuales) => [nueva, ...actuales]);
      setContenidoEvolucion(""); setFormEvolucion(false);
      setMensaje("Evolución guardada correctamente.");
    } catch (e) { setErrorEvolucion(detalleError(e)); }
    finally { setGuardandoEvolucion(false); }
  }

  function editar() {
    if (!seleccion) return;
    setForm({ nombre: seleccion.nombre, apellido: seleccion.apellido, dni: seleccion.dni ?? "", telefono: seleccion.telefono ?? "", email: seleccion.email ?? "", fecha_nacimiento: seleccion.fecha_nacimiento ?? "" });
    setEditando(true); setModal(true);
  }

  async function desactivar() {
    if (!seleccion) return;
    try {
      await desactivarPacienteProfesional(seleccion.id);
      setSeleccion(null); setConfirmar(false); setMensaje("Paciente desactivado correctamente.");
      await cargar(q);
    } catch (e) { setError(detalleError(e)); }
  }

  return <ProfesionalShell activo="pacientes" nombre={props.nombre} tituloTopbar="Pacientes"
    onAbrirInicio={props.onVolver} onAbrirAgenda={props.onAbrirAgenda} onAbrirPacientes={() => undefined}
    onAbrirDisponibilidad={props.onAbrirDisponibilidad} onAbrirPrestaciones={props.onAbrirPrestaciones} onAbrirPerfil={props.onAbrirPerfil} onCerrarSesion={props.onCerrarSesion}>
    <div className="pacientes-pagina">
      <header className="pacientes-cabecera">
        <div><span>Directorio profesional</span><h1>Pacientes</h1><p>Gestioná tus pacientes y consultá su historial de turnos.</p></div>
        <button type="button" className="pacientes-boton primario" onClick={() => { setEditando(false); setForm(FORM_VACIO); setModal(true); }}>Nuevo paciente</button>
      </header>
      {mensaje && <p role="status" className="pacientes-feedback exito">{mensaje}</p>}
      {error && <div role="alert" className="pacientes-feedback error"><span>{error}</span><button type="button" onClick={() => void cargar(q)}>Reintentar</button></div>}
      <label className="pacientes-buscador"><span>Buscar pacientes</span><input aria-label="Buscar pacientes" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Nombre, apellido, DNI o teléfono" /></label>
      {cargando ? <div className="pacientes-estado"><span className="pacientes-spinner"/><p>Cargando pacientes...</p></div>
      : pacientes.length === 0 ? <div className="pacientes-estado"><Icono nombre="usuario"/><h2>No hay pacientes para mostrar.</h2><p>{q ? "Probá con otra búsqueda." : "Creá tu primer paciente para empezar."}</p></div>
      : <ul className="pacientes-lista">{pacientes.map((paciente) => <li key={paciente.id}>
          <div className="pacientes-identidad"><span>{paciente.nombre.charAt(0)}{paciente.apellido.charAt(0)}</span><strong>{paciente.nombre} {paciente.apellido}</strong></div>
          <dl><div><dt>Teléfono</dt><dd>{paciente.telefono || "No informado"}</dd></div><div><dt>Email</dt><dd>{paciente.email || "No informado"}</dd></div><div><dt>DNI</dt><dd>{paciente.dni || "No informado"}</dd></div></dl>
          <button type="button" className="pacientes-boton enlace" onClick={() => void ver(paciente)}>Ver paciente <Icono nombre="flecha"/></button>
        </li>)}</ul>}
    </div>

    {seleccion && <><button type="button" className="paciente-detalle-fondo" aria-label="Cerrar detalle" onClick={() => setSeleccion(null)} />
      <aside className="paciente-detalle" aria-label={`Detalle de ${seleccion.nombre} ${seleccion.apellido}`}>
        <header><div><span>Paciente</span><h2>{seleccion.nombre} {seleccion.apellido}</h2></div><button type="button" className="detalle-cerrar" aria-label="Cerrar detalle" onClick={() => setSeleccion(null)}>×</button></header>
        <section className="detalle-datos"><h3>Datos personales</h3><dl><div><dt>Teléfono</dt><dd>{seleccion.telefono || "No informado"}</dd></div><div><dt>Email</dt><dd>{seleccion.email || "No informado"}</dd></div><div><dt>DNI</dt><dd>{seleccion.dni || "No informado"}</dd></div><div><dt>Nacimiento</dt><dd>{seleccion.fecha_nacimiento ? new Intl.DateTimeFormat("es-AR", { timeZone: "UTC" }).format(new Date(`${seleccion.fecha_nacimiento}T00:00:00Z`)) : "No informado"}</dd></div></dl></section>
        <div className="detalle-acciones"><button type="button" className="pacientes-boton secundario" onClick={editar}>Editar</button><button type="button" className="pacientes-boton destructivo" onClick={() => setConfirmar(true)}>Desactivar paciente</button></div>
        <section className="detalle-historial"><header><span>Actividad</span><h3>Historial de turnos</h3></header>
          {cargandoHistorial ? <p>Cargando historial...</p> : historial.length ? <ol>{historial.map((turno) => <li key={turno.id}><time dateTime={turno.fecha_hora}>{fechaHistorial(turno.fecha_hora)}</time><div><strong>{turno.prestacion_nombre}</strong><span className={`historial-estado estado-${turno.estado}`}>{etiquetaEstado(turno.estado)}</span></div></li>)}</ol> : <p>Sin turnos registrados.</p>}
        </section>
        <section className="detalle-evoluciones">
          <header><div><span>Información clínica</span><h3>Evoluciones</h3></div>{!formEvolucion && <button type="button" className="pacientes-boton primario" onClick={() => setFormEvolucion(true)}>Nueva evolución</button>}</header>
          {formEvolucion && <form className="evolucion-formulario" onSubmit={guardarEvolucion}>
            <label htmlFor="contenido-evolucion">Nueva evolución</label>
            <textarea id="contenido-evolucion" value={contenidoEvolucion} onChange={(e) => setContenidoEvolucion(e.target.value)} rows={6} autoFocus placeholder="Registrá la evolución clínica del paciente." />
            {errorEvolucion && <p role="alert" className="evolucion-error">{errorEvolucion}</p>}
            <div><button type="button" className="pacientes-boton secundario" onClick={() => { setFormEvolucion(false); setErrorEvolucion(""); }}>Cancelar</button><button className="pacientes-boton primario" disabled={guardandoEvolucion || !contenidoEvolucion.trim()}>{guardandoEvolucion ? "Guardando…" : "Guardar"}</button></div>
          </form>}
          {cargandoEvoluciones ? <p>Cargando evoluciones...</p> : evoluciones.length ? <ol>{evoluciones.map((evolucion) => <li key={evolucion.id}><header><time dateTime={evolucion.created_at}>{fechaHistorial(evolucion.created_at)}</time><strong>{evolucion.profesional_nombre}</strong></header><p>{evolucion.contenido}</p></li>)}</ol> : <div className="evoluciones-vacio"><p>Todavía no hay evoluciones registradas para este paciente.</p>{!formEvolucion && <button type="button" className="pacientes-boton enlace" onClick={() => setFormEvolucion(true)}>Crear la primera evolución</button>}</div>}
        </section>
      </aside></>}

    {confirmar && <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="desactivar-titulo"><div className="modal-paciente modal-confirmacion"><span className="modal-etiqueta">Acción sobre paciente</span><h2 id="desactivar-titulo">Desactivar paciente</h2><p>El paciente dejará de aparecer en tu listado activo. Sus turnos e historial se conservarán.</p><div className="modal-acciones"><button type="button" className="pacientes-boton secundario" onClick={() => setConfirmar(false)}>Cancelar</button><button type="button" className="pacientes-boton destructivo-solido" onClick={() => void desactivar()}>Desactivar</button></div></div></div>}

    {modal && <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="paciente-modal-titulo"><form className="modal-paciente" onSubmit={guardar}>
      <header className="modal-encabezado"><div><span className="modal-etiqueta">Datos básicos</span><h2 id="paciente-modal-titulo">{editando ? "Editar paciente" : "Nuevo paciente"}</h2><p>Completá la información necesaria para identificarlo.</p></div><button type="button" className="detalle-cerrar" aria-label="Cerrar" onClick={() => setModal(false)}>×</button></header>
      <div className="formulario-grilla">{([['nombre','Nombre *'],['apellido','Apellido *'],['dni','DNI'],['telefono','Teléfono'],['email','Email'],['fecha_nacimiento','Fecha de nacimiento']] as const).map(([clave, etiqueta]) => <label key={clave}><span>{etiqueta}</span><input type={clave === "email" ? "email" : clave === "fecha_nacimiento" ? "date" : "text"} required={clave === "nombre" || clave === "apellido"} value={form[clave]} onChange={(e) => setForm({ ...form, [clave]: e.target.value })}/></label>)}</div>
      <footer className="modal-acciones"><button type="button" className="pacientes-boton secundario" onClick={() => setModal(false)}>Cancelar</button><button className="pacientes-boton primario" disabled={guardando}>{guardando ? (editando ? "Guardando…" : "Creando…") : editando ? "Guardar cambios" : "Crear paciente"}</button></footer>
    </form></div>}
  </ProfesionalShell>;
}
