import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";

import "./DashboardProfesional.css";
import Icono from "./Icono";
import ProfesionalShell from "./ProfesionalShell";
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
  etiquetaFechaProximoTurno,
  fechaActualNegocio,
  formatearHoraTurno,
  ZONA_HORARIA_NEGOCIO,
} from "../utils/fechaTurno";
import {
  etiquetaPeriodo,
  minutosDesdeHora,
  periodoDesdeMinutos,
  type PeriodoDia,
} from "../utils/periodoDia";

type DashboardProfesionalProps = {
  nombre: string;
  onAbrirAgenda: () => void;
  onAbrirPacientes: () => void;
  onAbrirDisponibilidad: () => void;
  onAbrirPrestaciones: () => void;
  onAbrirPerfil: () => void;
  onCerrarSesion: () => void;
};

const ESTADOS_TERMINALES = ["cancelado", "finalizado", "ausente"];

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
  const hora = horaMinutosNegocio(ahora) / 60;
  if (hora >= 5 && hora < 12) return "Buen día";
  if (hora >= 12 && hora < 20) return "Buenas tardes";
  return "Buenas noches";
}

function diaSemanaNegocio(ahora: Date): number {
  const nombre = new Intl.DateTimeFormat("en-US", {
    timeZone: ZONA_HORARIA_NEGOCIO,
    weekday: "short",
  }).format(ahora);
  return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].indexOf(nombre);
}

function horaMinutosNegocio(fecha: Date): number {
  const partes = new Intl.DateTimeFormat("en-US", {
    timeZone: ZONA_HORARIA_NEGOCIO,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(fecha);
  const valores = Object.fromEntries(partes.map((parte) => [parte.type, parte.value]));
  return Number(valores.hour) * 60 + Number(valores.minute);
}

function periodoTurno(turno: Turno): PeriodoDia {
  return periodoDesdeMinutos(horaMinutosNegocio(new Date(turno.fecha_hora)));
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

function horarioTurno(turno: Turno): string {
  const inicio = formatearHoraTurno(turno.fecha_hora);
  return turno.fecha_fin ? `${inicio}–${formatearHoraTurno(turno.fecha_fin)}` : inicio;
}

function rangoPeriodo(items: Disponibilidad[], periodo: PeriodoDia): string {
  const franjas = items.filter((item) =>
    periodoDesdeMinutos(minutosDesdeHora(item.hora_inicio)) === periodo
  );
  if (franjas.length === 0) return "Sin disponibilidad";
  return franjas.map((item) =>
    `${item.hora_inicio.slice(0, 5)}–${item.hora_fin.slice(0, 5)}`
  ).join(" · ");
}

function dentroDeDisponibilidad(ahora: Date, items: Disponibilidad[]): boolean {
  const minutos = horaMinutosNegocio(ahora);
  return items.some((item) =>
    minutos >= minutosDesdeHora(item.hora_inicio) && minutos < minutosDesdeHora(item.hora_fin)
  );
}

function DashboardSkeleton() {
  return <div className="prof-skeleton" aria-label="Cargando agenda">
    <div className="prof-skeleton-proximo" />
    <div className="prof-skeleton-layout">
      <div className="prof-skeleton-agenda">
        <span /><span /><span /><span />
      </div>
      <div className="prof-skeleton-jornada" />
    </div>
  </div>;
}

export default function DashboardProfesional({
  nombre,
  onAbrirAgenda,
  onAbrirPacientes,
  onAbrirDisponibilidad,
  onAbrirPrestaciones,
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
  const [turnoExpandido, setTurnoExpandido] = useState<number | null>(null);

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
    .filter((turno) => !ESTADOS_TERMINALES.includes(turno.estado))
    .filter((turno) => new Date(turno.fecha_hora).getTime() >= ahora.getTime())
    .sort((a, b) => new Date(a.fecha_hora).getTime() - new Date(b.fecha_hora).getTime())[0], [ahora, turnos]);
  const disponibilidadHoy = disponibilidades.filter((item) => item.dia_semana === diaSemanaNegocio(ahora));
  const turnosManana = turnosHoy.filter((turno) => periodoTurno(turno) === "manana");
  const turnosTarde = turnosHoy.filter((turno) => periodoTurno(turno) === "tarde");
  const turnosNoche = turnosHoy.filter((turno) => periodoTurno(turno) === "noche");
  const resumen = {
    confirmados: turnosHoy.filter((turno) => turno.estado === "confirmado").length,
    pendientes: turnosHoy.filter((turno) => turno.estado === "reservado").length,
    resueltos: turnosHoy.filter((turno) => ESTADOS_TERMINALES.includes(turno.estado)).length,
  };
  const mostrarAhora = dentroDeDisponibilidad(ahora, disponibilidadHoy);

  async function actualizarTurno(turno: Turno, accion: "finalizar" | "ausente") {
    setErrorAccion("");
    setTurnoActualizando(turno.id);
    try {
      const actualizado = accion === "finalizar"
        ? await finalizarMiTurno(turno.id)
        : await marcarAusenteMiTurno(turno.id);
      setTurnos((actuales) => actuales.map((item) => item.id === actualizado.id ? actualizado : item));
      setTurnoExpandido(null);
    } catch (error) {
      setErrorAccion(detalleError(error, "No pudimos actualizar el turno."));
    } finally {
      setTurnoActualizando(null);
    }
  }

  function alternarTurno(turno: Turno) {
    if (ESTADOS_TERMINALES.includes(turno.estado) || turno.id === proximoTurno?.id) return;
    setTurnoExpandido((actual) => actual === turno.id ? null : turno.id);
  }

  function manejarTeclado(evento: React.KeyboardEvent<HTMLElement>, turno: Turno) {
    if (evento.key === "Enter" || evento.key === " ") {
      evento.preventDefault();
      alternarTurno(turno);
    }
  }

  function indicadorAhora(turnosPeriodo: Turno[]) {
    if (!mostrarAhora) return -1;
    const minutosAhora = horaMinutosNegocio(ahora);
    return turnosPeriodo.findIndex((turno) =>
      horaMinutosNegocio(new Date(turno.fecha_hora)) >= minutosAhora
    );
  }

  function renderTurno(turno: Turno) {
    const terminal = ESTADOS_TERMINALES.includes(turno.estado);
    const proximo = turno.id === proximoTurno?.id;
    const expandido = proximo || turnoExpandido === turno.id;
    const pasado = new Date(turno.fecha_fin ?? turno.fecha_hora).getTime() < ahora.getTime();
    const accionable = !terminal;

    return <li
      key={turno.id}
      className={`prof-turno estado-${turno.estado}${proximo ? " es-proximo" : ""}${pasado ? " es-pasado" : ""}${expandido ? " esta-expandido" : ""}`}
    >
      <article
        tabIndex={accionable ? 0 : undefined}
        aria-label={`${formatearHoraTurno(turno.fecha_hora)}, ${turno.paciente_nombre}, ${etiquetaEstado(turno.estado)}`}
        aria-expanded={accionable ? expandido : undefined}
        onClick={() => alternarTurno(turno)}
        onKeyDown={(evento) => manejarTeclado(evento, turno)}
      >
        <time dateTime={turno.fecha_hora}>{formatearHoraTurno(turno.fecha_hora)}</time>
        <span className="prof-turno-marca" aria-hidden="true" />
        <div className="prof-turno-contenido">
          <div className="prof-turno-identidad">
            <h3>{turno.paciente_nombre}</h3>
            <p>{turno.prestacion_nombre} · {turno.especialidad_nombre}</p>
            {turno.fecha_fin && <small>{horarioTurno(turno)}</small>}
            {turno.observaciones && terminal && <small>{turno.observaciones}</small>}
          </div>
          <span className="prof-estado"><i aria-hidden="true" />{etiquetaEstado(turno.estado)}</span>
          {accionable && <div className="prof-turno-acciones">
            <button
              type="button"
              disabled={turnoActualizando === turno.id}
              onClick={(evento) => { evento.stopPropagation(); void actualizarTurno(turno, "finalizar"); }}
            ><Icono nombre="check" />Finalizar</button>
            <button
              type="button"
              disabled={turnoActualizando === turno.id}
              onClick={(evento) => { evento.stopPropagation(); void actualizarTurno(turno, "ausente"); }}
            >Marcar ausente</button>
          </div>}
        </div>
      </article>
    </li>;
  }

  function renderPeriodo(periodo: PeriodoDia, items: Turno[]) {
    if (items.length === 0) return null;

    const posicionAhora = indicadorAhora(items);
    const ahoraPertenece = mostrarAhora && disponibilidadHoy.some((item) => {
      const inicio = minutosDesdeHora(item.hora_inicio);
      const esPeriodo = periodoDesdeMinutos(inicio) === periodo;
      const minutos = horaMinutosNegocio(ahora);
      return esPeriodo && minutos >= inicio && minutos < minutosDesdeHora(item.hora_fin);
    });

    return <section className="prof-periodo" aria-labelledby={`periodo-${periodo}`}>
      <header>
        <h3 id={`periodo-${periodo}`}><span />{etiquetaPeriodo(periodo)}</h3>
        <p>{rangoPeriodo(disponibilidadHoy, periodo)}</p>
      </header>
      <ol>
        {items.map((turno, indice) => <Fragment key={turno.id}>
          {ahoraPertenece && posicionAhora === indice && <li className="prof-ahora" role="status"><span>Ahora</span><i /></li>}
          {renderTurno(turno)}
        </Fragment>)}
        {ahoraPertenece && posicionAhora === -1 && <li className="prof-ahora" role="status"><span>Ahora</span><i /></li>}
      </ol>
    </section>;
  }

  const nombreCompleto = perfil ? `${perfil.nombre} ${perfil.apellido}` : nombre;
  return <ProfesionalShell
    activo="inicio"
    nombre={nombreCompleto}
    tituloTopbar="Hoy"
    onAbrirInicio={() => undefined}
    onAbrirAgenda={onAbrirAgenda}
    onAbrirPacientes={onAbrirPacientes}
    onAbrirDisponibilidad={onAbrirDisponibilidad}
    onAbrirPrestaciones={onAbrirPrestaciones}
    onAbrirPerfil={onAbrirPerfil}
    onCerrarSesion={onCerrarSesion}
    accionTopbar={<button type="button" className="prof-enlace-topbar" onClick={onAbrirAgenda}>Ver agenda completa <Icono nombre="flecha" /></button>}
  >
      <div className="prof-contenido">
        <section className="prof-saludo">
          <div><h1>{saludo(ahora)}, {perfil?.nombre ?? nombre}</h1><p>{fechaLarga(ahora)}</p></div>
          {!cargandoAgenda && !errorAgenda && <p className="prof-resumen-textual" aria-label="Resumen de la jornada">
            <strong>{turnosHoy.length}</strong> turnos <i /> <strong>{resumen.confirmados}</strong> confirmados <i /> <strong>{resumen.pendientes}</strong> pendiente{resumen.pendientes === 1 ? "" : "s"} <i /> <strong>{resumen.resueltos}</strong> resueltos
          </p>}
        </section>

        {cargandoAgenda ? <DashboardSkeleton /> : <>
          <section className="prof-proximo" aria-labelledby="proximo-titulo">
            {errorAgenda ? <p className="prof-texto-error">No pudimos consultar el próximo turno.</p>
            : proximoTurno ? <>
              <div className="prof-proximo-hora"><span>Próximo</span><span className="prof-proximo-fecha">{etiquetaFechaProximoTurno(proximoTurno.fecha_hora, ahora)}</span><time dateTime={proximoTurno.fecha_hora}>{formatearHoraTurno(proximoTurno.fecha_hora)}</time></div>
              <div className="prof-proximo-persona"><h2 id="proximo-titulo">{proximoTurno.paciente_nombre}</h2><p>{proximoTurno.prestacion_nombre}</p><small>{horarioTurno(proximoTurno)}</small></div>
              <div className={`prof-proximo-estado estado-${proximoTurno.estado}`}><span className="prof-estado"><i aria-hidden="true" />{etiquetaEstado(proximoTurno.estado)}</span><button type="button" onClick={onAbrirAgenda}>Ir a la agenda</button></div>
            </> : <div className="prof-proximo-vacio"><span>Próximo</span><h2 id="proximo-titulo">No hay más turnos próximos</h2><p>Tu agenda no tiene reservas futuras activas.</p></div>}
          </section>

          <div className="prof-layout">
            <section className="prof-agenda-seccion" aria-labelledby="agenda-hoy-titulo">
              <header><div><h2 id="agenda-hoy-titulo">Agenda de hoy</h2><p>{turnosHoy.length === 1 ? "1 turno programado" : `${turnosHoy.length} turnos programados`}</p></div><button type="button" onClick={onAbrirAgenda}>Ver toda</button></header>
              {errorAgenda ? <div className="prof-error" role="alert"><div><strong>No pudimos cargar tu agenda</strong><p>{errorAgenda}</p><button type="button" onClick={() => void cargarAgenda()}><Icono nombre="recargar" />Reintentar</button></div></div>
              : turnosHoy.length === 0 ? <div className="prof-vacio"><h3>Tu agenda está libre hoy</h3><p>No tenés turnos programados para esta jornada.</p><button type="button" onClick={onAbrirDisponibilidad}>Revisar disponibilidad</button></div>
              : <>{renderPeriodo("manana", turnosManana)}{renderPeriodo("tarde", turnosTarde)}{renderPeriodo("noche", turnosNoche)}</>}
              {errorAccion && <p className="prof-error-accion" role="alert">{errorAccion}</p>}
            </section>

            <aside className="prof-jornada" aria-labelledby="jornada-titulo">
              <span>Disponibilidad de hoy</span>
              <h2 id="jornada-titulo">Tu jornada</h2>
              {cargandoPerfil ? <div className="prof-jornada-cargando"><span /><span /></div>
              : errorDisponibilidad ? <p className="prof-texto-error">{errorDisponibilidad}</p>
              : <div className="prof-franjas">
                <div><small>Mañana</small><strong>{rangoPeriodo(disponibilidadHoy, "manana")}</strong></div>
                <div><small>Tarde</small><strong>{rangoPeriodo(disponibilidadHoy, "tarde")}</strong></div>
                <div><small>Noche</small><strong>{rangoPeriodo(disponibilidadHoy, "noche")}</strong></div>
              </div>}
              <div className="prof-jornada-resumen"><strong>{turnosHoy.length} turnos programados</strong><p>{resumen.confirmados} confirmados · {resumen.pendientes} pendiente{resumen.pendientes === 1 ? "" : "s"}</p></div>
              <button type="button" onClick={onAbrirDisponibilidad}>Configurar horarios</button>
            </aside>
          </div>
        </>}
      </div>
  </ProfesionalShell>;
}
