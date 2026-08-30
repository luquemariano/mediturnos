import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";

import "./AgendaPropia.css";
import GestionTurnoProfesional from "./GestionTurnoProfesional";
import Icono from "./Icono";
import ProfesionalShell from "./ProfesionalShell";
import NuevoTurnoProfesional from "./NuevoTurnoProfesional";
import AgendaSemana from "./AgendaSemana";
import AgendaMes from "./AgendaMes";
import { obtenerMisExcepciones } from "../services/disponibilidadService";
import type { DisponibilidadExcepcion } from "../types/disponibilidad";
import { mapaExcepciones } from "../utils/excepcionesAgenda";
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
  formatearHoraTurno,
} from "../utils/fechaTurno";
import { diaAnterior, diaSiguiente, diasGrillaMes, finSemana, formatearFechaCivil, formatearMes, formatearSemana, hoyNegocio, inicioSemana, mesAnterior, mesSiguiente, semanaAnterior, semanaSiguiente, type FechaCivil } from "../utils/calendario";

type AgendaPropiaProps = {
  tipo: "profesional" | "paciente";
  nombre?: string;
  onVolver: () => void;
  onAbrirPacientes?: () => void;
  onAbrirDisponibilidad?: () => void;
  onAbrirPrestaciones?: () => void;
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
  onAbrirPacientes = onVolver,
  onAbrirDisponibilidad = onVolver,
  onAbrirPrestaciones = onVolver,
  onAbrirPerfil = onVolver,
  onCerrarSesion = onVolver,
}: AgendaPropiaProps) {
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState("");
  const [errorAccion, setErrorAccion] = useState<{ id: number; mensaje: string } | null>(null);
  const [turnosActualizando, setTurnosActualizando] = useState<Set<number>>(() => new Set());
  const [turnoExpandido, setTurnoExpandido] = useState<number | null>(null);
  const [fechaSeleccionada, setFechaSeleccionada] = useState(() => hoyNegocio());
  const [tipoVista, setTipoVista] = useState<"dia" | "semana" | "mes">("dia");
  const [ahora] = useState(() => new Date());
  const [mostrarNuevoTurno, setMostrarNuevoTurno] = useState(false);
  const [mensajeExito, setMensajeExito] = useState("");
  const [gestionTurno, setGestionTurno] = useState<{ modo: "cancelar" | "reprogramar"; turno: Turno } | null>(null);
  const [errorGestion, setErrorGestion] = useState("");
  const [excepciones, setExcepciones] = useState<DisponibilidadExcepcion[]>([]);
  const rangoConsulta = useMemo(() => tipoVista === "semana"
    ? { desde: inicioSemana(fechaSeleccionada), hasta: finSemana(fechaSeleccionada) }
    : tipoVista === "mes"
      ? (() => { const dias = diasGrillaMes(fechaSeleccionada); return { desde: dias[0], hasta: dias[dias.length - 1] }; })()
      : { desde: fechaSeleccionada, hasta: fechaSeleccionada }, [fechaSeleccionada, tipoVista]);

  const cargar = useCallback(async () => {
    setCargando(true);
    setErrorCarga("");
    try {
      setTurnos(await (tipo === "profesional" ? obtenerMiAgendaProfesional(rangoConsulta) : obtenerMisTurnosPaciente()));
    } catch (motivo) {
      setErrorCarga(detalleError(motivo, tipo === "profesional" ? "No pudimos cargar tu agenda." : "No se pudieron cargar tus turnos."));
    } finally {
      setCargando(false);
    }
  }, [rangoConsulta, tipo]);
  useEffect(() => {
    if (tipo !== "profesional") return;
    void obtenerMisExcepciones(hoyNegocio()).then(setExcepciones, () => setExcepciones([]));
  }, [tipo]);
  const excepcionesPorFecha = useMemo(() => mapaExcepciones(excepciones), [excepciones]);

  useEffect(() => { void cargar(); }, [cargar]);

  const ordenados = useMemo(() => [...turnos].sort((a, b) =>
    new Date(a.fecha_hora).getTime() - new Date(b.fecha_hora).getTime()
  ), [turnos]);
  const grupos = useMemo(() => [[fechaSeleccionada, ordenados.filter((turno) => claveFechaNegocio(turno.fecha_hora) === fechaSeleccionada)] as [string, Turno[]]], [fechaSeleccionada, ordenados]);
  const proximoId = ordenados.find((turno) =>
    !TERMINALES.includes(turno.estado) && new Date(turno.fecha_hora).getTime() >= ahora.getTime()
  )?.id;

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

  function abrirGestionDesdeSemana(turno: Turno) {
    if (TERMINALES.includes(turno.estado)) return;
    setErrorGestion("");
    setGestionTurno({ modo: "reprogramar", turno });
  }

  function moverFecha(fecha: FechaCivil) {
    setFechaSeleccionada(fecha);
  }

  function moverPeriodo(fecha: FechaCivil) {
    setFechaSeleccionada(fecha);
  }

  return <ProfesionalShell
    activo="agenda"
    nombre={nombre}
    tituloTopbar="Mi agenda"
    onAbrirInicio={onVolver}
    onAbrirAgenda={() => undefined}
    onAbrirPacientes={onAbrirPacientes}
    onAbrirDisponibilidad={onAbrirDisponibilidad}
    onAbrirPrestaciones={onAbrirPrestaciones}
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

      <nav className="agenda-prof-selector" aria-label="Vista de agenda">
        <button type="button" aria-pressed={tipoVista === "dia"} onClick={() => setTipoVista("dia")}>Día</button>
        <button type="button" aria-pressed={tipoVista === "semana"} onClick={() => setTipoVista("semana")}>Semana</button>
        <button type="button" aria-pressed={tipoVista === "mes"} onClick={() => setTipoVista("mes")}>Mes</button>
      </nav>
      <nav className="agenda-prof-navegacion" aria-label="Navegación temporal">
        <button type="button" aria-label="Fecha anterior" onClick={() => moverPeriodo(tipoVista === "semana" ? semanaAnterior(fechaSeleccionada) : tipoVista === "mes" ? mesAnterior(fechaSeleccionada) : diaAnterior(fechaSeleccionada))}><Icono nombre="flecha" /></button>
        <strong>{tipoVista === "semana" ? formatearSemana(fechaSeleccionada) : tipoVista === "mes" ? formatearMes(fechaSeleccionada) : formatearFechaCivil(fechaSeleccionada)}</strong>
        <button type="button" aria-label="Fecha siguiente" onClick={() => moverPeriodo(tipoVista === "semana" ? semanaSiguiente(fechaSeleccionada) : tipoVista === "mes" ? mesSiguiente(fechaSeleccionada) : diaSiguiente(fechaSeleccionada))}><Icono nombre="flecha" /></button>
        <button type="button" className="agenda-prof-hoy" disabled={tipoVista === "dia" ? fechaSeleccionada === hoyNegocio() : tipoVista === "semana" ? inicioSemana(fechaSeleccionada) === inicioSemana(hoyNegocio()) : fechaSeleccionada.slice(0, 7) === hoyNegocio().slice(0, 7)} onClick={() => moverFecha(hoyNegocio())}>Hoy</button>
      </nav>

      {cargando ? (tipoVista === "semana" || tipoVista === "mes" ? <p className="agenda-semana-cargando" role="status">Cargando {tipoVista === "mes" ? "mes" : "semana"}…</p> : <AgendaSkeleton />) : errorCarga ? <section className="agenda-prof-estado" role="alert">
        <h2>No pudimos cargar tu agenda.</h2><p>{errorCarga}</p>
        <button type="button" onClick={() => void cargar()}><Icono nombre="recargar" />Reintentar</button>
      </section> : tipoVista === "semana" ? <AgendaSemana turnos={turnos} excepciones={excepcionesPorFecha} fecha={fechaSeleccionada} ahora={ahora} onSeleccionarDia={(dia) => { setFechaSeleccionada(dia); setTipoVista("dia"); }} onSeleccionarTurno={abrirGestionDesdeSemana} /> : tipoVista === "mes" ? <AgendaMes turnos={turnos} excepciones={excepcionesPorFecha} fecha={fechaSeleccionada} ahora={ahora} onSeleccionarDia={(dia) => { setFechaSeleccionada(dia); setTipoVista("dia"); }} /> : turnos.length === 0 ? <section className="agenda-prof-estado">
        <h2>No tenés turnos para este día.</h2>
        <p>Podés revisar otra fecha o crear un nuevo turno.</p>
      </section> : <>
        <div className="agenda-prof-grupos">
          {grupos.map(([clave, items]) => <section key={clave} id={`agenda-fecha-${clave}`} className="agenda-prof-grupo es-activo" aria-labelledby={`titulo-${clave}`}>
            <header>
              <h2 id={`titulo-${clave}`}>{formatearFechaCivil(fechaSeleccionada)}</h2>
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
