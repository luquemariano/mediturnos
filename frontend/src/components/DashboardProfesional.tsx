import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";

import "./DashboardProfesional.css";
import Icono from "./Icono";
import type { Disponibilidad } from "../types/disponibilidad";
import type { Profesional } from "../types/profesional";
import type { Turno } from "../types/turno";
import { obtenerDisponibilidadesProfesional } from "../services/disponibilidadService";
import { obtenerMiPerfilProfesional } from "../services/profesionalService";
import {
  finalizarMiTurno,
  marcarAusenteMiTurno,
  obtenerMiAgendaProfesional,
} from "../services/turnoService";
import {
  claveFechaNegocio,
  fechaActualNegocio,
  formatearHoraTurno,
  ZONA_HORARIA_NEGOCIO,
} from "../utils/fechaTurno";

type DashboardProfesionalProps = {
  nombre: string;
  onAbrirAgenda: () => void;
  onAbrirDisponibilidad: () => void;
  onAbrirPerfil: () => void;
  onCerrarSesion: () => void;
};

function detalleError(error: unknown, alternativo: string): string {
  if (axios.isAxiosError(error) && typeof error.response?.data?.detail === "string") {
    return error.response.data.detail;
  }
  return alternativo;
}

function fechaLarga(ahora: Date): string {
  const texto = new Intl.DateTimeFormat("es-AR", {
    timeZone: ZONA_HORARIA_NEGOCIO,
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(ahora);
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

function saludo(ahora: Date): string {
  const hora = Number(new Intl.DateTimeFormat("en-US", {
    timeZone: ZONA_HORARIA_NEGOCIO,
    hour: "2-digit",
    hour12: false,
  }).format(ahora));
  if (hora < 12) return "Buen día";
  if (hora < 20) return "Buenas tardes";
  return "Buenas noches";
}

function diaSemanaNegocio(ahora: Date): number {
  const nombre = new Intl.DateTimeFormat("en-US", {
    timeZone: ZONA_HORARIA_NEGOCIO,
    weekday: "short",
  }).format(ahora);
  return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].indexOf(nombre);
}

function etiquetaEstado(estado: Turno["estado"]): string {
  return {
    reservado: "Pendiente",
    confirmado: "Confirmado",
    cancelado: "Cancelado",
    ausente: "Ausente",
    finalizado: "Finalizado",
  }[estado];
}

function rangoDisponibilidad(items: Disponibilidad[]): string {
  if (items.length === 0) return "No tenés horarios configurados para hoy.";
  return `Hoy atendés ${items.map((item) =>
    `de ${item.hora_inicio.slice(0, 5)} a ${item.hora_fin.slice(0, 5)}`
  ).join(" y ")}.`;
}

function DashboardSkeleton() {
  return <div className="prof-skeleton" aria-label="Cargando agenda">
    <span className="prof-skeleton-linea ancha" />
    <span className="prof-skeleton-linea media" />
    <div className="prof-skeleton-resumen"><span/><span/><span/></div>
    <div className="prof-skeleton-grilla"><span/><span/></div>
  </div>;
}

export default function DashboardProfesional({
  nombre,
  onAbrirAgenda,
  onAbrirDisponibilidad,
  onAbrirPerfil,
  onCerrarSesion,
}: DashboardProfesionalProps) {
  const [ahora] = useState(() => new Date());
  const [perfil, setPerfil] = useState<Profesional | null>(null);
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [disponibilidades, setDisponibilidades] = useState<Disponibilidad[]>([]);
  const [cargandoAgenda, setCargandoAgenda] = useState(true);
  const [cargandoPerfil, setCargandoPerfil] = useState(true);
  const [errorAgenda, setErrorAgenda] = useState("");
  const [errorDisponibilidad, setErrorDisponibilidad] = useState("");
  const [errorAccion, setErrorAccion] = useState("");
  const [turnoActualizando, setTurnoActualizando] = useState<number | null>(null);

  const cargarAgenda = useCallback(async () => {
    setCargandoAgenda(true);
    setErrorAgenda("");
    try {
      setTurnos(await obtenerMiAgendaProfesional());
    } catch (error) {
      setErrorAgenda(detalleError(error, "No pudimos cargar tu agenda."));
    } finally {
      setCargandoAgenda(false);
    }
  }, []);

  const cargarPerfilYDisponibilidad = useCallback(async () => {
    setCargandoPerfil(true);
    setErrorDisponibilidad("");
    try {
      const datosPerfil = await obtenerMiPerfilProfesional();
      setPerfil(datosPerfil);
      try {
        setDisponibilidades(await obtenerDisponibilidadesProfesional(datosPerfil.id));
      } catch (error) {
        setErrorDisponibilidad(detalleError(error, "No pudimos cargar tus horarios."));
      }
    } catch (error) {
      setErrorDisponibilidad(detalleError(error, "No pudimos cargar tu perfil profesional."));
    } finally {
      setCargandoPerfil(false);
    }
  }, []);

  useEffect(() => {
    void cargarAgenda();
    void cargarPerfilYDisponibilidad();
  }, [cargarAgenda, cargarPerfilYDisponibilidad]);

  const hoy = fechaActualNegocio(ahora);
  const turnosHoy = useMemo(() => turnos
    .filter((turno) => claveFechaNegocio(turno.fecha_hora) === hoy)
    .sort((a, b) => new Date(a.fecha_hora).getTime() - new Date(b.fecha_hora).getTime()), [hoy, turnos]);
  const proximoTurno = useMemo(() => turnos
    .filter((turno) => !["cancelado", "finalizado", "ausente"].includes(turno.estado))
    .filter((turno) => new Date(turno.fecha_hora).getTime() >= ahora.getTime())
    .sort((a, b) => new Date(a.fecha_hora).getTime() - new Date(b.fecha_hora).getTime())[0], [ahora, turnos]);
  const disponibilidadHoy = disponibilidades.filter((item) => item.dia_semana === diaSemanaNegocio(ahora));
  const resumen = {
    confirmados: turnosHoy.filter((turno) => turno.estado === "confirmado").length,
    pendientes: turnosHoy.filter((turno) => turno.estado === "reservado").length,
    cancelados: turnosHoy.filter((turno) => turno.estado === "cancelado").length,
  };

  async function actualizarTurno(turno: Turno, accion: "finalizar" | "ausente") {
    setErrorAccion("");
    setTurnoActualizando(turno.id);
    try {
      const actualizado = accion === "finalizar"
        ? await finalizarMiTurno(turno.id)
        : await marcarAusenteMiTurno(turno.id);
      setTurnos((actuales) => actuales.map((item) => item.id === actualizado.id ? actualizado : item));
    } catch (error) {
      setErrorAccion(detalleError(error, "No pudimos actualizar el turno."));
    } finally {
      setTurnoActualizando(null);
    }
  }

  const nombreCompleto = perfil ? `${perfil.nombre} ${perfil.apellido}` : nombre;
  const iniciales = nombreCompleto.split(" ").slice(0, 2).map((parte) => parte.charAt(0)).join("").toUpperCase();

  return <div className="prof-app-shell">
    <aside className="prof-sidebar">
      <div className="prof-marca"><span className="prof-marca-simbolo">M</span><strong>MediTurnos</strong></div>
      <nav aria-label="Navegación profesional">
        <button className="activo" type="button" aria-current="page"><Icono nombre="inicio"/>Inicio</button>
        <button type="button" onClick={onAbrirAgenda}><Icono nombre="agenda"/>Mi agenda</button>
        <button type="button" onClick={onAbrirDisponibilidad}><Icono nombre="reloj"/>Mi disponibilidad</button>
        <button type="button" onClick={onAbrirPerfil}><Icono nombre="perfil"/>Mi perfil</button>
      </nav>
      <div className="prof-sidebar-perfil">
        <span className="prof-avatar">{iniciales || "P"}</span>
        <div><strong>{nombreCompleto}</strong><small>Profesional</small></div>
        <button type="button" onClick={onCerrarSesion} aria-label="Cerrar sesión"><Icono nombre="salir"/></button>
      </div>
    </aside>

    <main className="prof-main">
      <header className="prof-topbar">
        <div className="prof-marca-movil"><span className="prof-marca-simbolo">M</span><strong>MediTurnos</strong></div>
        <span className="prof-topbar-titulo">Inicio</span>
        <button type="button" className="prof-boton-secundario" onClick={onAbrirAgenda}>Ver agenda completa</button>
        <button type="button" className="prof-avatar prof-avatar-movil" onClick={onAbrirPerfil} aria-label="Abrir mi perfil">{iniciales || "P"}</button>
      </header>

      <div className="prof-contenido">
        <section className="prof-saludo">
          <div><h1>{saludo(ahora)}, {perfil?.nombre ?? nombre}</h1><p>{fechaLarga(ahora)}</p></div>
          {!cargandoAgenda && !errorAgenda && <p className="prof-contexto">{turnosHoy.length === 1 ? "Tenés 1 turno programado para hoy." : `Tenés ${turnosHoy.length} turnos programados para hoy.`}</p>}
        </section>

        {cargandoAgenda ? <DashboardSkeleton /> : <>
          <section className="prof-resumen" aria-label="Resumen de la jornada">
            <div className="confirmados"><span/><strong>{resumen.confirmados}</strong><small>Confirmados</small></div>
            <div className="pendientes"><span/><strong>{resumen.pendientes}</strong><small>Pendientes</small></div>
            <div className="cancelados"><span/><strong>{resumen.cancelados}</strong><small>Cancelados</small></div>
          </section>

          <div className="prof-layout">
            <section className="prof-agenda-seccion" aria-labelledby="agenda-hoy-titulo">
              <header><div><h2 id="agenda-hoy-titulo">Agenda de hoy</h2><p>{turnosHoy.length === 1 ? "1 turno" : `${turnosHoy.length} turnos`}</p></div><button type="button" onClick={onAbrirAgenda}>Ver toda <Icono nombre="flecha"/></button></header>
              {errorAgenda ? <div className="prof-error" role="alert"><Icono nombre="alerta"/><div><strong>No pudimos cargar tu agenda</strong><p>{errorAgenda}</p><button type="button" onClick={() => void cargarAgenda()}><Icono nombre="recargar"/>Reintentar</button></div></div>
              : turnosHoy.length === 0 ? <div className="prof-vacio"><Icono nombre="agenda"/><h3>Tu agenda está libre hoy</h3><p>No tenés turnos programados para esta jornada.</p><button type="button" onClick={onAbrirDisponibilidad}>Revisar disponibilidad</button></div>
              : <ol className="prof-timeline">{turnosHoy.map((turno) => <li key={turno.id} className={`estado-${turno.estado}`}>
                <time dateTime={turno.fecha_hora}>{formatearHoraTurno(turno.fecha_hora)}</time><span className="prof-timeline-marca"/><article>
                  <div className="prof-turno-principal"><div><h3>{turno.paciente_nombre}</h3><p>{turno.prestacion_nombre} · {turno.especialidad_nombre}</p></div><span className={`prof-estado estado-${turno.estado}`}>{etiquetaEstado(turno.estado)}</span></div>
                  {turno.observaciones && <small>Tiene observaciones</small>}
                  {["reservado", "confirmado"].includes(turno.estado) && <div className="prof-turno-acciones">
                    <button type="button" disabled={turnoActualizando === turno.id} onClick={() => void actualizarTurno(turno, "finalizar")}><Icono nombre="check"/>Finalizar</button>
                    <button type="button" disabled={turnoActualizando === turno.id} onClick={() => void actualizarTurno(turno, "ausente")}>Marcar ausente</button>
                  </div>}
                </article>
              </li>)}</ol>}
              {errorAccion && <p className="prof-error-accion" role="alert">{errorAccion}</p>}
            </section>

            <aside className="prof-columna-lateral">
              <section className="prof-proximo" aria-labelledby="proximo-titulo">
                <header><span>Próximo turno</span>{proximoTurno && <span className={`prof-estado estado-${proximoTurno.estado}`}>{etiquetaEstado(proximoTurno.estado)}</span>}</header>
                {errorAgenda ? <p className="prof-texto-error">No pudimos consultar el próximo turno.</p>
                : proximoTurno ? <><time id="proximo-titulo" dateTime={proximoTurno.fecha_hora}>{formatearHoraTurno(proximoTurno.fecha_hora)}</time><h2>{proximoTurno.paciente_nombre}</h2><p>{proximoTurno.prestacion_nombre}</p><small>{claveFechaNegocio(proximoTurno.fecha_hora) === hoy ? "Hoy" : new Intl.DateTimeFormat("es-AR", {timeZone: ZONA_HORARIA_NEGOCIO, weekday:"long", day:"numeric", month:"short"}).format(new Date(proximoTurno.fecha_hora))}</small><button type="button" onClick={onAbrirAgenda}>Ver detalle <Icono nombre="flecha"/></button></>
                : <div className="prof-proximo-vacio"><Icono nombre="check"/><h2 id="proximo-titulo">No hay más turnos próximos</h2><p>Tu agenda no tiene reservas futuras activas.</p></div>}
              </section>

              <section className="prof-disponibilidad-resumen">
                <Icono nombre="reloj"/><div><h2>Mi disponibilidad</h2>{cargandoPerfil ? <span className="prof-skeleton-linea corta"/> : errorDisponibilidad ? <p className="prof-texto-error">{errorDisponibilidad}</p> : <p>{rangoDisponibilidad(disponibilidadHoy)}</p>}<button type="button" onClick={onAbrirDisponibilidad}>Configurar horarios <Icono nombre="flecha"/></button></div>
              </section>
            </aside>
          </div>
        </>}
      </div>
    </main>

    <nav className="prof-nav-movil" aria-label="Navegación principal">
      <button className="activo" type="button" aria-current="page"><Icono nombre="inicio"/><span>Inicio</span></button>
      <button type="button" onClick={onAbrirAgenda}><Icono nombre="agenda"/><span>Agenda</span></button>
      <button type="button" onClick={onAbrirDisponibilidad}><Icono nombre="reloj"/><span>Disponibilidad</span></button>
      <button type="button" onClick={onAbrirPerfil}><Icono nombre="perfil"/><span>Perfil</span></button>
    </nav>
  </div>;
}
