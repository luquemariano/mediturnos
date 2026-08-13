import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";

import "./AgendaPropia.css";
import GestionTurnoProfesional from "./GestionTurnoProfesional";
import Icono from "./Icono";
import ProfesionalShell from "./ProfesionalShell";
import NuevoTurnoProfesional from "./NuevoTurnoProfesional";
import type { Turno } from "../types/turno";
import {
  cancelarMiTurno,
  cancelarMiTurnoProfesional,
  finalizarMiTurno,
  marcarAusenteMiTurno,
  obtenerMiAgendaProfesional,
  obtenerMisTurnosPaciente,
} from "../services/turnoService";
import {
  claveFechaNegocio,
  fechaActualNegocio,
  formatearFechaTurno,
  formatearHoraTurno,
  ZONA_HORARIA_NEGOCIO,
} from "../utils/fechaTurno";

type AgendaPropiaProps = {
  tipo: "profesional" | "paciente";
  nombre?: string;
  onVolver: () => void;
  onAbrirDisponibilidad?: () => void;
  onAbrirPerfil?: () => void;
  onCerrarSesion?: () => void;
};

const TERMINALES = ["cancelado", "ausente", "finalizado"];

function detalleError(error: unknown, alternativo = "No se pudo cargar la información."): string {
  if (axios.isAxiosError(error) && typeof error.response?.data?.detail === "string") {
    return error.response.data.detail;
  }
  return alternativo;
}

function etiquetaEstado(estado: Turno["estado"]): string {
  return estado === "reservado" ? "Pendiente" : estado.charAt(0).toUpperCase() + estado.slice(1);
}

function rangoTurno(turno: Turno): string {
  const inicio = formatearHoraTurno(turno.fecha_hora);
  return turno.fecha_fin ? `${inicio}–${formatearHoraTurno(turno.fecha_fin)}` : inicio;
}

function etiquetaFecha(turno: Turno, hoy: string): string {
  const clave = claveFechaNegocio(turno.fecha_hora);
  const fecha = new Date(turno.fecha_hora);
  const actual = new Date();
  const formateadorAnio = new Intl.DateTimeFormat("es-AR", {
    timeZone: ZONA_HORARIA_NEGOCIO,
    year: "numeric",
  });
  const anioFecha = formateadorAnio.format(fecha);
  const anioActual = formateadorAnio.format(actual);
  const texto = formatearFechaTurno(turno.fecha_hora).replace(",", "");
  const sinAnio = texto.replace(new RegExp(` de ${anioFecha}$`), "");
  const fechaTexto = anioFecha === anioActual ? sinAnio : texto;
  return `${clave === hoy ? "Hoy · " : ""}${fechaTexto}`;
}

function AgendaPaciente({ turnos, cargando, error, onVolver, actualizar }: {
  turnos: Turno[];
  cargando: boolean;
  error: string;
  onVolver: () => void;
  actualizar: (turno: Turno, accion: "cancelar") => Promise<void>;
}) {
  return <main className="pagina-dashboard">
    <section className="dashboard">
      <header className="dashboard-encabezado">
        <h1>Mis turnos</h1>
        <button type="button" className="boton-cerrar-sesion" onClick={onVolver}>Volver al panel</button>
      </header>
      {cargando && <p>Cargando turnos...</p>}
      {error && <p role="alert">{error}</p>}
      {!cargando && !error && turnos.length === 0 && <p>No hay turnos registrados.</p>}
      <div className="agenda-lista">
        {turnos.map((turno) => <article className="turno-tarjeta" key={turno.id}>
          <div className="turno-informacion">
            <h2>{turno.prestacion_nombre}</h2>
            <p>{turno.paciente_nombre} · {turno.fecha_hora}</p>
            <strong>{turno.estado}</strong>
          </div>
          <div className="turno-acciones">
            {["reservado", "confirmado"].includes(turno.estado) && <button type="button" onClick={() => void actualizar(turno, "cancelar")}>Cancelar turno</button>}
          </div>
        </article>)}
      </div>
    </section>
  </main>;
}

function AgendaSkeleton() {
  return <div className="agenda-prof-skeleton" aria-label="Cargando agenda">
    <span className="agenda-prof-skeleton-titulo" />
    <span className="agenda-prof-skeleton-nav" />
    {[0, 1].map((grupo) => <div key={grupo} className="agenda-prof-skeleton-grupo">
      <span />
      <i /><i /><i />
    </div>)}
  </div>;
}

export default function AgendaPropia({
  tipo,
  nombre = "Profesional",
  onVolver,
  onAbrirDisponibilidad = onVolver,
  onAbrirPerfil = onVolver,
  onCerrarSesion = onVolver,
}: AgendaPropiaProps) {
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState("");
  const [errorAccion, setErrorAccion] = useState<{ id: number; mensaje: string } | null>(null);
  const [turnosActualizando, setTurnosActualizando] = useState<Set<number>>(() => new Set());
  const [turnoExpandido, setTurnoExpandido] = useState<number | null>(null);
  const [fechaActiva, setFechaActiva] = useState<string | null>(null);
  const [ahora] = useState(() => new Date());
  const [mostrarNuevoTurno, setMostrarNuevoTurno] = useState(false);
  const [mensajeExito, setMensajeExito] = useState("");
  const [gestionTurno, setGestionTurno] = useState<{ modo: "cancelar" | "reprogramar"; turno: Turno } | null>(null);
  const [errorGestion, setErrorGestion] = useState("");

  const cargar = useCallback(async () => {
    setCargando(true);
    setErrorCarga("");
    try {
      setTurnos(await (tipo === "profesional" ? obtenerMiAgendaProfesional() : obtenerMisTurnosPaciente()));
    } catch (motivo) {
      setErrorCarga(detalleError(motivo, tipo === "profesional" ? "No pudimos cargar tu agenda." : "No se pudieron cargar tus turnos."));
    } finally {
      setCargando(false);
    }
  }, [tipo]);

  useEffect(() => { void cargar(); }, [cargar]);

  const ordenados = useMemo(() => [...turnos].sort((a, b) =>
    new Date(a.fecha_hora).getTime() - new Date(b.fecha_hora).getTime()
  ), [turnos]);
  const grupos = useMemo(() => {
    const mapa = new Map<string, Turno[]>();
    ordenados.forEach((turno) => {
      const clave = claveFechaNegocio(turno.fecha_hora);
      mapa.set(clave, [...(mapa.get(clave) ?? []), turno]);
    });
    return [...mapa.entries()];
  }, [ordenados]);
  const hoy = fechaActualNegocio(ahora);
  const proximoId = ordenados.find((turno) =>
    !TERMINALES.includes(turno.estado) && new Date(turno.fecha_hora).getTime() >= ahora.getTime()
  )?.id;
  const indiceActivo = Math.max(0, grupos.findIndex(([clave]) => clave === (fechaActiva ?? (grupos.some(([clave]) => clave === hoy) ? hoy : grupos[0]?.[0]))));
  const grupoActivo = grupos[indiceActivo];

  async function actualizar(turno: Turno, accion: "cancelar" | "finalizar" | "ausente") {
    if (turnosActualizando.has(turno.id)) return;
    setErrorAccion(null);
    setTurnosActualizando((actuales) => new Set(actuales).add(turno.id));
    try {
      const actualizado = accion === "cancelar"
        ? await cancelarMiTurno(turno.id)
        : accion === "finalizar"
          ? await finalizarMiTurno(turno.id)
          : await marcarAusenteMiTurno(turno.id);
      setTurnos((actuales) => actuales.map((item) => item.id === actualizado.id ? actualizado : item));
      setTurnoExpandido(null);
    } catch (motivo) {
      setErrorAccion({ id: turno.id, mensaje: detalleError(motivo, "No pudimos actualizar el turno.") });
    } finally {
      setTurnosActualizando((actuales) => {
        const siguientes = new Set(actuales);
        siguientes.delete(turno.id);
        return siguientes;
      });
    }
  }

  async function cancelarComoProfesional() {
    if (!gestionTurno || turnosActualizando.has(gestionTurno.turno.id)) return;
    const turno = gestionTurno.turno;
    setErrorGestion("");
    setTurnosActualizando((actuales) => new Set(actuales).add(turno.id));
    try {
      const actualizado = await cancelarMiTurnoProfesional(turno.id);
      setTurnos((actuales) => actuales.map((item) => item.id === actualizado.id ? actualizado : item));
      setGestionTurno(null);
      setTurnoExpandido(null);
      setMensajeExito("Turno cancelado correctamente.");
    } catch (motivo) {
      setErrorGestion(detalleError(motivo, "No pudimos cancelar el turno."));
    } finally {
      setTurnosActualizando((actuales) => {
        const siguientes = new Set(actuales);
        siguientes.delete(turno.id);
        return siguientes;
      });
    }
  }

  if (tipo === "paciente") {
    return <AgendaPaciente turnos={turnos} cargando={cargando} error={errorCarga} onVolver={onVolver} actualizar={actualizar} />;
  }

  function seleccionarTurno(turno: Turno) {
    if (TERMINALES.includes(turno.estado) || turno.id === proximoId) return;
    setTurnoExpandido((actual) => actual === turno.id ? null : turno.id);
  }

  function moverFecha(desplazamiento: number) {
    const siguiente = grupos[indiceActivo + desplazamiento];
    if (!siguiente) return;
    setFechaActiva(siguiente[0]);
    document.getElementById(`agenda-fecha-${siguiente[0]}`)?.scrollIntoView?.({ behavior: "smooth", block: "start" });
  }

  return <ProfesionalShell
    activo="agenda"
    nombre={nombre}
    tituloTopbar="Mi agenda"
    onAbrirInicio={onVolver}
    onAbrirAgenda={() => undefined}
    onAbrirDisponibilidad={onAbrirDisponibilidad}
    onAbrirPerfil={onAbrirPerfil}
    onCerrarSesion={onCerrarSesion}
    accionTopbar={<button type="button" className="prof-enlace-topbar" onClick={onVolver}>Volver a inicio <Icono nombre="flecha" /></button>}
  >
    <div className="agenda-prof-contenido">
      <header className="agenda-prof-cabecera">
        <div><h1>Mi agenda</h1><p>Consultá y gestioná tus próximos turnos.</p></div>
        <div className="agenda-prof-cabecera-acciones">
          {!cargando && !errorCarga && <p><strong>{turnos.length}</strong> turno{turnos.length === 1 ? "" : "s"} en agenda</p>}
          <button type="button" onClick={() => { setMensajeExito(""); setMostrarNuevoTurno(true); }}>+ Nuevo turno</button>
        </div>
      </header>

      {mensajeExito && <p className="agenda-prof-exito" role="status">{mensajeExito}</p>}

      {cargando ? <AgendaSkeleton /> : errorCarga ? <section className="agenda-prof-estado" role="alert">
        <h2>No pudimos cargar tu agenda.</h2><p>{errorCarga}</p>
        <button type="button" onClick={() => void cargar()}><Icono nombre="recargar" />Reintentar</button>
      </section> : turnos.length === 0 ? <section className="agenda-prof-estado">
        <h2>Todavía no tenés turnos programados.</h2>
        <p>Cuando se asignen turnos, aparecerán ordenados por fecha y hora.</p>
      </section> : <>
        <nav className="agenda-prof-navegacion" aria-label="Navegación temporal">
          <button type="button" aria-label="Fecha anterior" disabled={indiceActivo === 0} onClick={() => moverFecha(-1)}><Icono nombre="flecha" /></button>
          <strong>{grupoActivo ? etiquetaFecha(grupoActivo[1][0], hoy) : "Agenda"}</strong>
          <button type="button" aria-label="Fecha siguiente" disabled={indiceActivo === grupos.length - 1} onClick={() => moverFecha(1)}><Icono nombre="flecha" /></button>
          <button type="button" className="agenda-prof-hoy" onClick={() => {
            const indiceHoy = grupos.findIndex(([clave]) => clave === hoy);
            if (indiceHoy >= 0) moverFecha(indiceHoy - indiceActivo);
          }}>Hoy</button>
        </nav>

        <div className="agenda-prof-grupos">
          {grupos.map(([clave, items]) => <section key={clave} id={`agenda-fecha-${clave}`} className={`agenda-prof-grupo${grupoActivo?.[0] === clave ? " es-activo" : ""}`} aria-labelledby={`titulo-${clave}`}>
            <header>
              <h2 id={`titulo-${clave}`}>{etiquetaFecha(items[0], hoy)}</h2>
              <p>{items.length} turno{items.length === 1 ? "" : "s"}</p>
            </header>
            <ol>
              {items.map((turno) => {
                const terminal = TERMINALES.includes(turno.estado);
                const proximo = turno.id === proximoId;
                const expandido = proximo || turnoExpandido === turno.id;
                const pasado = new Date(turno.fecha_fin ?? turno.fecha_hora).getTime() < ahora.getTime();
                const actualizando = turnosActualizando.has(turno.id);
                return <li key={turno.id} className={`agenda-prof-turno estado-${turno.estado}${proximo ? " es-proximo" : ""}${pasado ? " es-pasado" : ""}${expandido ? " esta-expandido" : ""}`}>
                  <article
                    tabIndex={!terminal ? 0 : undefined}
                    aria-label={`${rangoTurno(turno)}, ${turno.paciente_nombre}, ${etiquetaEstado(turno.estado)}`}
                    aria-expanded={!terminal ? expandido : undefined}
                    onClick={() => seleccionarTurno(turno)}
                    onKeyDown={(evento) => {
                      if (evento.key === "Enter" || evento.key === " ") {
                        evento.preventDefault(); seleccionarTurno(turno);
                      }
                    }}
                  >
                    <time dateTime={turno.fecha_hora}>{rangoTurno(turno)}</time>
                    <span className="agenda-prof-marca" aria-hidden="true" />
                    <div className="agenda-prof-datos">
                      <div className="agenda-prof-identidad">
                        <h3>{turno.paciente_nombre}</h3>
                        <p>{turno.prestacion_nombre} · {turno.especialidad_nombre}</p>
                        {turno.observaciones && <p className="agenda-prof-observacion">{turno.observaciones}</p>}
                      </div>
                      <span className="agenda-prof-estado"><i aria-hidden="true" />{etiquetaEstado(turno.estado)}</span>
                      {!terminal && <div className="agenda-prof-acciones">
                        <button type="button" disabled={actualizando} onClick={(evento) => { evento.stopPropagation(); void actualizar(turno, "finalizar"); }}><Icono nombre="check" />{actualizando ? "Actualizando…" : "Finalizar"}</button>
                        <button type="button" disabled={actualizando} onClick={(evento) => { evento.stopPropagation(); void actualizar(turno, "ausente"); }}>Marcar ausente</button>
                        <button type="button" disabled={actualizando} onClick={(evento) => { evento.stopPropagation(); setErrorGestion(""); setGestionTurno({ modo: "reprogramar", turno }); }}>Reprogramar</button>
                        <button type="button" className="agenda-prof-accion-cancelar" disabled={actualizando} onClick={(evento) => { evento.stopPropagation(); setErrorGestion(""); setGestionTurno({ modo: "cancelar", turno }); }}>Cancelar</button>
                        {actualizando && <span className="sr-only" role="status">Actualizando turno de {turno.paciente_nombre}</span>}
                      </div>}
                    </div>
                  </article>
                  {errorAccion?.id === turno.id && <p className="agenda-prof-error-accion" role="alert">{errorAccion.mensaje}</p>}
                </li>;
              })}
            </ol>
          </section>)}
        </div>
      </>}
    </div>
    {mostrarNuevoTurno && <NuevoTurnoProfesional onCerrar={() => setMostrarNuevoTurno(false)} onCreado={(turno) => {
      setTurnos((actuales) => [...actuales, turno]);
      setMostrarNuevoTurno(false);
      setMensajeExito("Turno creado correctamente.");
    }} />}
    {gestionTurno && <GestionTurnoProfesional
      modo={gestionTurno.modo}
      turno={gestionTurno.turno}
      guardando={turnosActualizando.has(gestionTurno.turno.id)}
      errorExterno={errorGestion}
      onCerrar={() => { if (!turnosActualizando.has(gestionTurno.turno.id)) setGestionTurno(null); }}
      onCancelar={cancelarComoProfesional}
      onReprogramado={(actualizado) => {
        setTurnos((actuales) => actuales.map((item) => item.id === actualizado.id ? actualizado : item));
        setGestionTurno(null);
        setTurnoExpandido(null);
        setMensajeExito("Turno reprogramado correctamente.");
      }}
    />}
  </ProfesionalShell>;
}
