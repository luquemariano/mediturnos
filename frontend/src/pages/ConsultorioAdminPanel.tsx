import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";

import Icono from "../components/Icono";
import ProfesionalShell from "../components/ProfesionalShell";
import {
  actualizarModuloConsultorio,
  actualizarReglaConsultorio,
  crearInvitacionConsultorio,
  crearModuloExtraordinario,
  crearReglaConsultorio,
  enviarInvitacionConsultorio,
  listarConsultoriosAdministrados,
  listarInvitacionesConsultorio,
  listarModulosConsultorio,
  listarProfesionalesConsultorio,
  listarReglasConsultorio,
  listarSalasConsultorio,
  revocarInvitacionConsultorio,
  suspenderModuloConsultorio,
} from "../services/consultorioService";
import type {
  ConsultorioAdministrado,
  InvitacionConsultorio,
  ModuloConsultorio,
  ModuloSemanalPayload,
  ProfesionalConsultorio,
  ReglaModuloConsultorio,
  SalaConsultorio,
} from "../types/consultorio";
import "./ConsultorioAdminPanel.css";

type Pestaña = "ocupacion" | "modulos" | "invitaciones";
type ModuloBorrador = { sala_id: string; dia_semana: string; hora_inicio: string; duracion_minutos: string; vigente_desde: string; vigente_hasta: string };

const DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
const zonaPredeterminada = "America/Argentina/Buenos_Aires";

function fechaClave(fecha: Date, zona: string): string {
  const parts = new Intl.DateTimeFormat("en-CA", { timeZone: zona, year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(fecha);
  const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${value.year}-${value.month}-${value.day}`;
}

function moverFecha(clave: string, dias: number): string {
  const fecha = new Date(`${clave}T12:00:00Z`);
  fecha.setUTCDate(fecha.getUTCDate() + dias);
  return fecha.toISOString().slice(0, 10);
}

function inicioSemana(clave: string): string {
  const fecha = new Date(`${clave}T12:00:00Z`);
  const lunesOffset = (fecha.getUTCDay() + 6) % 7;
  fecha.setUTCDate(fecha.getUTCDate() - lunesOffset);
  return fecha.toISOString().slice(0, 10);
}

function isoZonado(fecha: string, hora: string, zona: string): string {
  const objetivo = Date.parse(`${fecha}T${hora}:00Z`);
  let instante = objetivo;
  for (let intento = 0; intento < 4; intento += 1) {
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: zona, year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23",
    }).formatToParts(new Date(instante));
    const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    const mostradoComoUtc = Date.UTC(Number(value.year), Number(value.month) - 1, Number(value.day), Number(value.hour), Number(value.minute), Number(value.second));
    const diferencia = objetivo - mostradoComoUtc;
    instante += diferencia;
    if (diferencia === 0) break;
  }
  return new Date(instante).toISOString();
}

function horaEnZona(valor: string, zona: string): string {
  return new Intl.DateTimeFormat("es-AR", { timeZone: zona, hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(new Date(valor));
}

function fechaHoraLocal(valor: string, zona: string): string {
  const parts = new Intl.DateTimeFormat("en-CA", { timeZone: zona, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(new Date(valor));
  const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${value.year}-${value.month}-${value.day}T${value.hour}:${value.minute}`;
}

function etiquetaDia(clave: string, zona: string): string {
  const fecha = new Date(`${clave}T12:00:00Z`);
  return new Intl.DateTimeFormat("es-AR", { timeZone: zona, weekday: "short", day: "numeric", month: "short" }).format(fecha);
}

function mensajeError(error: unknown, respaldo: string): string {
  if (!axios.isAxiosError(error)) return respaldo;
  const detail = error.response?.data?.detail;
  if (detail && typeof detail === "object" && typeof detail.turnos_afectados === "number") {
    const cantidad = detail.turnos_afectados;
    return `El cambio está bloqueado porque afecta a ${cantidad} ${cantidad === 1 ? "turno" : "turnos"}. No se modificó ningún turno.`;
  }
  return typeof detail === "string" ? detail : respaldo;
}

function borradorModulo(salaId = "", fecha = ""): ModuloBorrador {
  return { sala_id: salaId, dia_semana: "0", hora_inicio: "09:00", duracion_minutos: "240", vigente_desde: fecha, vigente_hasta: "" };
}

function payloadModulo(modulo: ModuloBorrador): ModuloSemanalPayload {
  return {
    sala_id: Number(modulo.sala_id), dia_semana: Number(modulo.dia_semana),
    hora_inicio: modulo.hora_inicio, duracion_minutos: Number(modulo.duracion_minutos),
    vigente_desde: modulo.vigente_desde,
    ...(modulo.vigente_hasta ? { vigente_hasta: modulo.vigente_hasta } : {}),
  };
}

function estadoEtiqueta(estado: string): string {
  return ({ activa: "Ocupada", suspendida: "Suspendida", cancelada: "Liberada", preparacion: "Preparación", pendiente: "Pendiente", aceptada: "Aceptada", revocada: "Revocada", expirada: "Vencida" } as Record<string, string>)[estado] ?? estado;
}

export default function ConsultorioAdminPanel({ nombre, onVolver, onCerrarSesion }: { nombre: string; onVolver: () => void; onCerrarSesion: () => void }) {
  const [consultorios, setConsultorios] = useState<ConsultorioAdministrado[]>([]);
  const [consultorioId, setConsultorioId] = useState<number | null>(null);
  const [salas, setSalas] = useState<SalaConsultorio[]>([]);
  const [profesionales, setProfesionales] = useState<ProfesionalConsultorio[]>([]);
  const [reglas, setReglas] = useState<ReglaModuloConsultorio[]>([]);
  const [modulos, setModulos] = useState<ModuloConsultorio[]>([]);
  const [invitaciones, setInvitaciones] = useState<InvitacionConsultorio[]>([]);
  const [semana, setSemana] = useState(() => inicioSemana(fechaClave(new Date(), zonaPredeterminada)));
  const [salaFiltro, setSalaFiltro] = useState("todas");
  const [pestaña, setPestaña] = useState<Pestaña>("ocupacion");
  const [cargando, setCargando] = useState(true);
  const [errorCarga, setErrorCarga] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [errorAccion, setErrorAccion] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [recurrencia, setRecurrencia] = useState<ModuloBorrador>(borradorModulo());
  const [extraFecha, setExtraFecha] = useState("");
  const [extraInicio, setExtraInicio] = useState("09:00");
  const [extraFin, setExtraFin] = useState("13:00");
  const [extraSala, setExtraSala] = useState("");
  const [extraProfesional, setExtraProfesional] = useState("");
  const [reglaEditando, setReglaEditando] = useState<number | null>(null);
  const [efectivaDesde, setEfectivaDesde] = useState("");
  const [horaNueva, setHoraNueva] = useState("09:00");
  const [duracionNueva, setDuracionNueva] = useState("240");
  const [salaNueva, setSalaNueva] = useState("");
  const [profesionalNuevo, setProfesionalNuevo] = useState("");
  const [moduloEditando, setModuloEditando] = useState<number | null>(null);
  const [moduloFechaNueva, setModuloFechaNueva] = useState("");
  const [moduloInicioNuevo, setModuloInicioNuevo] = useState("09:00");
  const [moduloFinNuevo, setModuloFinNuevo] = useState("13:00");
  const [moduloSalaNueva, setModuloSalaNueva] = useState("");
  const [moduloProfesionalNuevo, setModuloProfesionalNuevo] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteNombre, setInviteNombre] = useState("");
  const [inviteModulos, setInviteModulos] = useState<ModuloBorrador[]>([borradorModulo()]);

  const consultorio = consultorios.find((item) => item.id === consultorioId) ?? null;
  const zona = consultorio?.zona_horaria ?? zonaPredeterminada;
  const semanaDias = useMemo(() => Array.from({ length: 7 }, (_, index) => moverFecha(semana, index)), [semana]);

  useEffect(() => {
    let vigente = true;
    setCargando(true);
    void listarConsultoriosAdministrados().then((items) => {
      if (!vigente) return;
      setConsultorios(items);
      if (items.length > 0) {
        setConsultorioId(items[0].id);
        setSemana(inicioSemana(fechaClave(new Date(), items[0].zona_horaria)));
      }
      setCargando(false);
    }).catch(() => {
      if (vigente) { setErrorCarga("No pudimos verificar tu acceso al consultorio."); setCargando(false); }
    });
    return () => { vigente = false; };
  }, []);

  const cargarDatos = useCallback(async () => {
    if (!consultorioId || !consultorio) return;
    setCargando(true); setErrorCarga("");
    const desde = isoZonado(semana, "00:00", zona);
    const hasta = isoZonado(moverFecha(semana, 7), "00:00", zona);
    try {
      const [salasData, profesionalesData, reglasData, modulosData, invitacionesData] = await Promise.all([
        listarSalasConsultorio(consultorioId), listarProfesionalesConsultorio(consultorioId),
        listarReglasConsultorio(consultorioId), listarModulosConsultorio(consultorioId, desde, hasta),
        listarInvitacionesConsultorio(consultorioId),
      ]);
      setSalas(salasData); setProfesionales(profesionalesData); setReglas(reglasData);
      setModulos(modulosData); setInvitaciones(invitacionesData);
      if (salaFiltro !== "todas" && !salasData.some((sala) => String(sala.id) === salaFiltro)) setSalaFiltro("todas");
    } catch (error) {
      setErrorCarga(mensajeError(error, "No pudimos cargar la ocupación y la configuración del consultorio."));
    } finally { setCargando(false); }
  }, [consultorioId, consultorio, semana, zona, salaFiltro]);

  useEffect(() => { void cargarDatos(); }, [cargarDatos]);

  useEffect(() => {
    if (!consultorio) return;
    const salaId = salas[0]?.id ? String(salas[0].id) : "";
    setRecurrencia((actual) => ({ ...actual, sala_id: actual.sala_id || salaId, duracion_minutos: String(consultorio.duracion_modulo_minutos) }));
    setExtraSala((actual) => actual || salaId);
    setModuloSalaNueva((actual) => actual || salaId);
    setInviteModulos((actual) => actual.map((item) => ({ ...item, sala_id: item.sala_id || salaId, duracion_minutos: String(consultorio.duracion_modulo_minutos) })));
    setExtraFecha((actual) => actual || fechaClave(new Date(), consultorio.zona_horaria));
  }, [consultorio, salas]);

  const ejecutarAccion = useCallback(async (accion: () => Promise<unknown>, exito: string) => {
    setGuardando(true); setMensaje(""); setErrorAccion("");
    try { await accion(); setMensaje(exito); await cargarDatos(); }
    catch (error) { setErrorAccion(mensajeError(error, "No se pudo completar el cambio. Revisá los datos e intentá nuevamente.")); }
    finally { setGuardando(false); }
  }, [cargarDatos]);

  async function crearRecurrencia(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); if (!consultorioId || !recurrencia.sala_id || profesionales.length === 0) return;
    const form = evento.currentTarget;
    const profesionalId = Number(new FormData(form).get("profesional_id"));
    await ejecutarAccion(() => crearReglaConsultorio(consultorioId, { ...payloadModulo(recurrencia), profesional_id: profesionalId }), "La recurrencia quedó configurada.");
  }

  async function crearExtraordinario(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); if (!consultorioId) return;
    const profesionalId = Number(extraProfesional);
    await ejecutarAccion(() => crearModuloExtraordinario(consultorioId, { sala_id: Number(extraSala), profesional_id: profesionalId, fecha_inicio: isoZonado(extraFecha, extraInicio, zona), fecha_fin: isoZonado(extraFecha, extraFin, zona) }), "El módulo extraordinario quedó reservado.");
  }

  async function guardarCambioRegla(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); if (!consultorioId || reglaEditando === null) return;
    if (!window.confirm("El cambio se aplicará desde la fecha indicada. Si afecta turnos, el sistema lo bloqueará y no los modificará. ¿Continuar?")) return;
    const payload: Record<string, unknown> = { vigente_desde: efectivaDesde, hora_inicio: horaNueva, duracion_minutos: Number(duracionNueva), sala_id: Number(salaNueva), profesional_id: Number(profesionalNuevo) };
    await ejecutarAccion(() => actualizarReglaConsultorio(consultorioId, reglaEditando, payload), "La recurrencia cambió desde la fecha indicada.");
    setReglaEditando(null);
  }

  async function guardarCambioModulo(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); if (!consultorioId || moduloEditando === null) return;
    if (!window.confirm("El cambio se aplicará sólo a esta fecha. Si afecta turnos, el sistema lo bloqueará y no los modificará. ¿Continuar?")) return;
    const fechaInicio = moduloFechaNueva.slice(0, 10);
    const fechaFin = moduloFinNuevo <= moduloInicioNuevo ? moverFecha(fechaInicio, 1) : fechaInicio;
    await ejecutarAccion(() => actualizarModuloConsultorio(consultorioId, moduloEditando, {
      sala_id: Number(moduloSalaNueva), profesional_id: Number(moduloProfesionalNuevo),
      fecha_inicio: isoZonado(fechaInicio, moduloInicioNuevo, zona),
      fecha_fin: isoZonado(fechaFin, moduloFinNuevo, zona),
    }), "El módulo de esa fecha fue actualizado.");
    setModuloEditando(null);
  }

  async function prepararInvitacion(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault(); if (!consultorioId) return;
    const payload = inviteModulos.map((item) => payloadModulo(item));
    await ejecutarAccion(() => crearInvitacionConsultorio(consultorioId, { email: inviteEmail, ...(inviteNombre.trim() ? { nombre_visible: inviteNombre.trim() } : {}), modulos: payload }), "La invitación quedó preparada con sus módulos reservados.");
    setInviteEmail(""); setInviteNombre("");
    setInviteModulos([borradorModulo(salas[0] ? String(salas[0].id) : "", fechaClave(new Date(), zona))]);
  }

  async function accionInvitacion(invite: InvitacionConsultorio, accion: "enviar" | "reenviar" | "revocar") {
    if (!consultorioId) return;
    const confirmacion = accion === "revocar"
      ? `Se liberarán los módulos futuros de ${invite.email}. ¿Revocar la invitación?`
      : `${accion === "reenviar" ? "Se enviará un nuevo enlace a" : "Enviar invitación a"} ${invite.email}. ¿Continuar?`;
    if (!window.confirm(confirmacion)) return;
    await ejecutarAccion(async () => {
      if (accion === "revocar") return revocarInvitacionConsultorio(consultorioId, invite.id);
      return enviarInvitacionConsultorio(consultorioId, invite.id, accion === "reenviar");
    }, accion === "revocar" ? "La invitación fue revocada y la reserva liberada." : "La invitación fue enviada.");
  }

  if (cargando && consultorios.length === 0) return <main className="pagina-login"><p role="status">Verificando acceso al consultorio…</p></main>;
  if (errorCarga && consultorios.length === 0) return <main className="pagina-login"><section className="acceso-publico consultorio-denegado"><h1>Consultorio no disponible</h1><p>{errorCarga}</p><button type="button" onClick={onVolver}>Volver a tu agenda profesional</button></section></main>;
  if (consultorios.length === 0 || consultorioId === null || !consultorio) return <main className="pagina-login"><section className="acceso-publico consultorio-denegado"><h1>Consultorio no disponible</h1><p>No encontramos un consultorio que administres.</p><button type="button" onClick={onVolver}>Volver a tu agenda profesional</button></section></main>;

  const modulosFiltrados = modulos.filter((item) => salaFiltro === "todas" || String(item.sala_id) === salaFiltro);
  const invitacionesActivas = invitaciones.filter((item) => ["preparacion", "pendiente"].includes(item.estado));
  const hoy = fechaClave(new Date(), zona);

  return <ProfesionalShell
    activo="consultorio" modoConsultorio
    nombre={nombre} tituloTopbar="Administración del consultorio"
    onAbrirInicio={onVolver} onAbrirAgenda={onVolver} onAbrirPacientes={onVolver}
    onAbrirDisponibilidad={onVolver} onAbrirPrestaciones={onVolver} onAbrirPerfil={onVolver}
    onAbrirConsultorio={() => undefined} onCerrarSesion={onCerrarSesion}
    accionTopbar={<button type="button" className="prof-enlace-topbar" onClick={onVolver}>Volver a mi agenda profesional <Icono nombre="flecha" /></button>}
  >
    <div className="prof-contenido consultorio-admin">
      <header className="consultorio-admin__cabecera">
        <div><p className="consultorio-admin__eyebrow">Espacio compartido</p><h1>{consultorio.nombre}</h1><p>Administrá la ocupación física sin acceder a agendas ni información clínica de otras profesionales.</p></div>
        {consultorios.length > 1 && <label className="consultorio-admin__selector">Consultorio<select value={consultorioId ?? ""} onChange={(event) => setConsultorioId(Number(event.target.value))}>{consultorios.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select></label>}
      </header>

      <nav className="consultorio-admin__tabs" aria-label="Secciones de administración">
        {([ ["ocupacion", "Ocupación semanal"], ["modulos", "Módulos"], ["invitaciones", "Invitaciones"] ] as [Pestaña, string][]).map(([id, label]) => <button type="button" key={id} className={pestaña === id ? "activo" : ""} aria-current={pestaña === id ? "page" : undefined} onClick={() => { setPestaña(id); setMensaje(""); setErrorAccion(""); }}>{label}</button>)}
      </nav>

      {mensaje && <p className="consultorio-admin__mensaje" role="status">{mensaje}</p>}
      {errorAccion && <p className="consultorio-admin__error" role="alert">{errorAccion}</p>}
      {errorCarga && <div className="consultorio-admin__error" role="alert"><span>{errorCarga}</span><button type="button" onClick={() => void cargarDatos()}>Reintentar</button></div>}
      {cargando && <p className="consultorio-admin__cargando" role="status">Actualizando información…</p>}

      {pestaña === "ocupacion" && <section className="consultorio-admin__panel" aria-labelledby="consultorio-agenda-titulo">
        <div className="consultorio-admin__agenda-toolbar">
          <div><h2 id="consultorio-agenda-titulo">Agenda de ocupación</h2><p>Semana del {etiquetaDia(semana, zona)} · zona {zona}</p></div>
          <div className="consultorio-admin__controles-agenda">
            <label>Sala<select aria-label="Filtrar por sala" value={salaFiltro} onChange={(event) => setSalaFiltro(event.target.value)}><option value="todas">Todas las salas</option>{salas.map((sala) => <option key={sala.id} value={sala.id}>{sala.nombre}</option>)}</select></label>
            <div className="consultorio-admin__semana-controles"><button type="button" aria-label="Semana anterior" onClick={() => setSemana((value) => moverFecha(value, -7))}>←</button><button type="button" onClick={() => setSemana(inicioSemana(hoy))}>Esta semana</button><button type="button" aria-label="Semana siguiente" onClick={() => setSemana((value) => moverFecha(value, 7))}>→</button></div>
          </div>
        </div>
        <ul className="consultorio-admin__leyenda" aria-label="Estados de ocupación"><li><i className="ocupada" />Ocupada</li><li><i className="pendiente" />Invitación pendiente</li><li><i className="liberada" />Suspendida o liberada</li></ul>
        {salas.length === 0 ? <div className="consultorio-admin__vacio"><h3>No hay salas configuradas</h3><p>Configurá una sala para empezar a organizar los módulos.</p></div> : <div className="consultorio-admin__semana" aria-label="Ocupación semanal por día y sala">
          {semanaDias.map((dia, index) => {
            const items = modulosFiltrados.filter((item) => fechaClave(new Date(item.fecha_inicio), zona) === dia).sort((a, b) => a.fecha_inicio.localeCompare(b.fecha_inicio));
            return <section key={dia} className="consultorio-admin__dia" aria-labelledby={`consultorio-dia-${index}`}>
              <header><h3 id={`consultorio-dia-${index}`}>{DIAS[index]}</h3><time dateTime={dia}>{etiquetaDia(dia, zona)}</time></header>
              {items.length ? <ul>{items.map((item) => <li key={item.id} className={`consultorio-admin__bloque estado-${item.estado} ${item.profesional_id === null ? "es-invitacion" : ""}`}>
                <strong>{horaEnZona(item.fecha_inicio, zona)}–{horaEnZona(item.fecha_fin, zona)}</strong>
                <span>{item.sala_nombre}</span>
                <span>{item.profesional_id === null ? "Invitación pendiente" : item.profesional_nombre}</span>
                <small>{item.profesional_id === null ? "Reserva pendiente" : estadoEtiqueta(item.estado)}</small>
              </li>)}</ul> : <p className="consultorio-admin__sin-modulos">Sin módulos</p>}
            </section>;
          })}
        </div>}
        <p className="consultorio-admin__privacidad">La vista muestra únicamente reservas de espacio. No incluye turnos ni datos de pacientes.</p>
      </section>}

      {pestaña === "modulos" && <div className="consultorio-admin__modulos">
        <section className="consultorio-admin__panel" aria-labelledby="consultorio-recurrencia-titulo">
          <header className="consultorio-admin__seccion-header"><div><h2 id="consultorio-recurrencia-titulo">Nueva recurrencia semanal</h2><p>Reservá uno o más horarios semanales para una profesional vinculada.</p></div></header>
          <form className="consultorio-admin__formulario" onSubmit={(event) => void crearRecurrencia(event)}>
            <label>Profesional<select name="profesional_id" required defaultValue=""><option value="" disabled>Elegí una profesional</option>{profesionales.map((item) => <option key={item.profesional_id} value={item.profesional_id}>{item.nombre}</option>)}</select></label>
            <label>Sala<select required value={recurrencia.sala_id} onChange={(event) => setRecurrencia({ ...recurrencia, sala_id: event.target.value })}>{salas.filter((item) => item.estado === "activa").map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select></label>
            <label>Día<select value={recurrencia.dia_semana} onChange={(event) => setRecurrencia({ ...recurrencia, dia_semana: event.target.value })}>{DIAS.map((dia, index) => <option key={dia} value={index}>{dia}</option>)}</select></label>
            <label>Desde<input type="date" min={hoy} required value={recurrencia.vigente_desde} onChange={(event) => setRecurrencia({ ...recurrencia, vigente_desde: event.target.value })} /></label>
            <label>Hora de inicio<input type="time" required value={recurrencia.hora_inicio} onChange={(event) => setRecurrencia({ ...recurrencia, hora_inicio: event.target.value })} /></label>
            <label>Duración (minutos)<input type="number" min="1" max="1440" required value={recurrencia.duracion_minutos} onChange={(event) => setRecurrencia({ ...recurrencia, duracion_minutos: event.target.value })} /></label>
            <label>Vigente hasta (opcional)<input type="date" min={recurrencia.vigente_desde || hoy} value={recurrencia.vigente_hasta} onChange={(event) => setRecurrencia({ ...recurrencia, vigente_hasta: event.target.value })} /></label>
            <button type="submit" disabled={guardando || profesionales.length === 0 || salas.length === 0}>Crear módulo recurrente</button>
          </form>
          {profesionales.length === 0 && <p className="consultorio-admin__ayuda">No hay profesionales vinculadas disponibles para asignar.</p>}
        </section>

        <section className="consultorio-admin__panel" aria-labelledby="consultorio-extra-titulo">
          <header className="consultorio-admin__seccion-header"><div><h2 id="consultorio-extra-titulo">Módulo extraordinario</h2><p>Reservá un horario puntual dentro del horizonte disponible.</p></div></header>
          <form className="consultorio-admin__formulario" onSubmit={(event) => void crearExtraordinario(event)}>
            <label>Profesional<select required value={extraProfesional} onChange={(event) => setExtraProfesional(event.target.value)}><option value="" disabled>Elegí una profesional</option>{profesionales.map((item) => <option key={item.profesional_id} value={item.profesional_id}>{item.nombre}</option>)}</select></label>
            <label>Sala<select required value={extraSala} onChange={(event) => setExtraSala(event.target.value)}>{salas.filter((item) => item.estado === "activa").map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select></label>
            <label>Fecha<input type="date" min={hoy} required value={extraFecha} onChange={(event) => setExtraFecha(event.target.value)} /></label>
            <label>Desde<input type="time" required value={extraInicio} onChange={(event) => setExtraInicio(event.target.value)} /></label>
            <label>Hasta<input type="time" required value={extraFin} onChange={(event) => setExtraFin(event.target.value)} /></label>
            <button type="submit" disabled={guardando || profesionales.length === 0 || salas.length === 0}>Reservar espacio</button>
          </form>
        </section>

        <section className="consultorio-admin__panel" aria-labelledby="consultorio-reglas-titulo">
          <header className="consultorio-admin__seccion-header"><div><h2 id="consultorio-reglas-titulo">Recurrencias vigentes</h2><p>Los cambios se aplican desde una fecha futura y se validan contra los turnos existentes.</p></div></header>
          {reglas.length === 0 ? <p className="consultorio-admin__vacio">Todavía no hay recurrencias activas.</p> : <ul className="consultorio-admin__lista-reglas">{reglas.map((regla) => <li key={regla.id}>
            <div><strong>{DIAS[regla.dia_semana]} · {regla.hora_inicio.slice(0, 5)} · {regla.duracion_minutos} min</strong><span>{regla.sala_nombre} · {regla.invitacion_pendiente ? "Invitación pendiente" : regla.profesional_nombre}</span><small>Desde {regla.vigente_desde}{regla.vigente_hasta ? ` hasta ${regla.vigente_hasta}` : " · sin fecha de cierre"}</small></div>
            {regla.profesional_id !== null && <button type="button" disabled={guardando} onClick={() => { setReglaEditando(regla.id); setEfectivaDesde(moverFecha(hoy, 1) > regla.vigente_desde ? moverFecha(hoy, 1) : regla.vigente_desde); setHoraNueva(regla.hora_inicio.slice(0, 5)); setDuracionNueva(String(regla.duracion_minutos)); setSalaNueva(String(regla.sala_id)); setProfesionalNuevo(String(regla.profesional_id)); }}>Cambiar desde una fecha</button>}
          </li>)}</ul>}
          {reglaEditando !== null && <form className="consultorio-admin__formulario consultorio-admin__formulario--edicion" onSubmit={(event) => void guardarCambioRegla(event)}>
            <h3>Nuevo tramo de recurrencia</h3>
            <label>Aplicar desde<input type="date" min={moverFecha(hoy, 1)} required value={efectivaDesde} onChange={(event) => setEfectivaDesde(event.target.value)} /></label>
            <label>Profesional<select value={profesionalNuevo} required onChange={(event) => setProfesionalNuevo(event.target.value)}>{profesionales.map((item) => <option key={item.profesional_id} value={item.profesional_id}>{item.nombre}</option>)}</select></label>
            <label>Sala<select value={salaNueva} required onChange={(event) => setSalaNueva(event.target.value)}>{salas.filter((item) => item.estado === "activa").map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select></label>
            <label>Hora<input type="time" required value={horaNueva} onChange={(event) => setHoraNueva(event.target.value)} /></label>
            <label>Duración<input type="number" min="1" max="1440" required value={duracionNueva} onChange={(event) => setDuracionNueva(event.target.value)} /></label>
            <div className="consultorio-admin__acciones-form"><button type="submit" disabled={guardando}>Confirmar cambio</button><button type="button" className="secundario" onClick={() => setReglaEditando(null)}>Cancelar</button></div>
          </form>}
        </section>

        <section className="consultorio-admin__panel" aria-labelledby="consultorio-ocurrencias-titulo">
          <header className="consultorio-admin__seccion-header"><div><h2 id="consultorio-ocurrencias-titulo">Cambios para una fecha</h2><p>Podés reprogramar o suspender una ocurrencia concreta. Los turnos nunca se cancelan automáticamente.</p></div></header>
          {modulos.length === 0 ? <p className="consultorio-admin__vacio">No hay ocurrencias en esta semana. Elegí otra semana en la pestaña de ocupación para revisar sus módulos.</p> : <ul className="consultorio-admin__lista-reglas">{modulos.filter((item) => item.estado === "activa" && item.profesional_id !== null).map((item) => <li key={item.id}>
            <div><strong>{etiquetaDia(fechaClave(new Date(item.fecha_inicio), zona), zona)} · {horaEnZona(item.fecha_inicio, zona)}–{horaEnZona(item.fecha_fin, zona)}</strong><span>{item.sala_nombre} · {item.profesional_nombre}</span><small>{item.origen === "extraordinaria" ? "Extraordinario" : "Recurrente"}</small></div>
            <div className="consultorio-admin__acciones-fila"><button type="button" disabled={guardando} onClick={() => { setModuloEditando(item.id); setModuloFechaNueva(fechaHoraLocal(item.fecha_inicio, zona)); setModuloInicioNuevo(horaEnZona(item.fecha_inicio, zona)); setModuloFinNuevo(horaEnZona(item.fecha_fin, zona)); setModuloSalaNueva(String(item.sala_id)); setModuloProfesionalNuevo(String(item.profesional_id)); }}>Cambiar</button><button type="button" className="secundario" disabled={guardando} onClick={() => { if (window.confirm("Se suspenderá este módulo si no tiene turnos comprometidos. ¿Continuar?")) void ejecutarAccion(() => suspenderModuloConsultorio(consultorioId, item.id), "El módulo fue suspendido."); }}>Suspender</button></div>
          </li>)}</ul>}
          {moduloEditando !== null && <form className="consultorio-admin__formulario consultorio-admin__formulario--edicion" onSubmit={(event) => void guardarCambioModulo(event)}>
            <h3>Editar una ocurrencia</h3>
            <label>Fecha<input type="date" min={hoy} required value={moduloFechaNueva.slice(0, 10)} onChange={(event) => setModuloFechaNueva(`${event.target.value}T${moduloInicioNuevo}`)} /></label>
            <label>Desde<input type="time" required value={moduloInicioNuevo} onChange={(event) => setModuloInicioNuevo(event.target.value)} /></label>
            <label>Hasta<input type="time" required value={moduloFinNuevo} onChange={(event) => setModuloFinNuevo(event.target.value)} /></label>
            <label>Profesional<select value={moduloProfesionalNuevo} required onChange={(event) => setModuloProfesionalNuevo(event.target.value)}>{profesionales.map((item) => <option key={item.profesional_id} value={item.profesional_id}>{item.nombre}</option>)}</select></label>
            <label>Sala<select value={moduloSalaNueva} required onChange={(event) => setModuloSalaNueva(event.target.value)}>{salas.filter((item) => item.estado === "activa").map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}</select></label>
            <div className="consultorio-admin__acciones-form"><button type="submit" disabled={guardando}>Guardar cambios</button><button type="button" className="secundario" onClick={() => setModuloEditando(null)}>Cancelar</button></div>
          </form>}
        </section>
      </div>}

      {pestaña === "invitaciones" && <div className="consultorio-admin__invitaciones">
        <section className="consultorio-admin__panel" aria-labelledby="consultorio-preparar-invitacion-titulo">
          <header className="consultorio-admin__seccion-header"><div><h2 id="consultorio-preparar-invitacion-titulo">Preparar una invitación</h2><p>Definí la plaza y sus módulos antes de enviar el enlace. La preparación reserva el espacio.</p></div></header>
          <form className="consultorio-admin__formulario" onSubmit={(event) => void prepararInvitacion(event)}>
            <label>Correo electrónico<input type="email" required value={inviteEmail} onChange={(event) => setInviteEmail(event.target.value)} /></label>
            <label>Nombre visible (opcional)<input type="text" maxLength={160} value={inviteNombre} onChange={(event) => setInviteNombre(event.target.value)} /></label>
            <div className="consultorio-admin__modulos-invitacion"><h3>Módulos semanales</h3>{inviteModulos.map((item, index) => <fieldset className="consultorio-admin__modulo-invitacion" key={index}><legend>Módulo {index + 1}</legend>
              <label>Sala<select required value={item.sala_id} onChange={(event) => setInviteModulos((actual) => actual.map((row, rowIndex) => rowIndex === index ? { ...row, sala_id: event.target.value } : row))}>{salas.filter((sala) => sala.estado === "activa").map((sala) => <option key={sala.id} value={sala.id}>{sala.nombre}</option>)}</select></label>
              <label>Día<select value={item.dia_semana} onChange={(event) => setInviteModulos((actual) => actual.map((row, rowIndex) => rowIndex === index ? { ...row, dia_semana: event.target.value } : row))}>{DIAS.map((dia, diaIndex) => <option key={dia} value={diaIndex}>{dia}</option>)}</select></label>
              <label>Desde<input type="date" min={hoy} required value={item.vigente_desde} onChange={(event) => setInviteModulos((actual) => actual.map((row, rowIndex) => rowIndex === index ? { ...row, vigente_desde: event.target.value } : row))} /></label>
              <label>Hora<input type="time" required value={item.hora_inicio} onChange={(event) => setInviteModulos((actual) => actual.map((row, rowIndex) => rowIndex === index ? { ...row, hora_inicio: event.target.value } : row))} /></label>
              <label>Duración<input type="number" min="1" max="1440" required value={item.duracion_minutos} onChange={(event) => setInviteModulos((actual) => actual.map((row, rowIndex) => rowIndex === index ? { ...row, duracion_minutos: event.target.value } : row))} /></label>
              {inviteModulos.length > 1 && <button type="button" className="secundario" onClick={() => setInviteModulos((actual) => actual.filter((_, rowIndex) => rowIndex !== index))}>Quitar módulo</button>}
            </fieldset>)}
            <button type="button" className="secundario consultorio-admin__agregar-modulo" disabled={inviteModulos.length >= 28} onClick={() => setInviteModulos((actual) => [...actual, borradorModulo(salas[0] ? String(salas[0].id) : "", hoy)])}>Agregar otro módulo semanal</button></div>
            <button type="submit" disabled={guardando || salas.length === 0}>Preparar invitación</button>
          </form>
        </section>

        <section className="consultorio-admin__panel" aria-labelledby="consultorio-invitaciones-lista-titulo">
          <header className="consultorio-admin__seccion-header"><div><h2 id="consultorio-invitaciones-lista-titulo">Invitaciones</h2><p>{invitacionesActivas.length} plaza{invitacionesActivas.length === 1 ? " activa" : "s activas"} reservada{invitacionesActivas.length === 1 ? "" : "s"}.</p></div></header>
          {invitaciones.length === 0 ? <p className="consultorio-admin__vacio">Todavía no hay invitaciones.</p> : <div className="consultorio-admin__tabla-contenedor"><table className="consultorio-admin__tabla"><thead><tr><th scope="col">Invitado</th><th scope="col">Estado</th><th scope="col">Vence</th><th scope="col">Módulos reservados</th><th scope="col">Acciones</th></tr></thead><tbody>{invitaciones.map((invite) => <tr key={invite.id}><th scope="row">{invite.nombre_visible || invite.email}<small>{invite.nombre_visible ? invite.email : ""}</small></th><td><span className={`consultorio-admin__estado estado-${invite.estado}`}>{estadoEtiqueta(invite.estado)}</span></td><td>{invite.vence_en ? new Intl.DateTimeFormat("es-AR", { timeZone: zona, dateStyle: "medium" }).format(new Date(invite.vence_en)) : "—"}</td><td>{invite.modulos_reservados}</td><td><div className="consultorio-admin__acciones-fila">
            {invite.estado === "preparacion" && <button type="button" disabled={guardando} onClick={() => void accionInvitacion(invite, "enviar")}>Enviar</button>}
            {invite.estado === "pendiente" && <><button type="button" disabled={guardando} onClick={() => void accionInvitacion(invite, "reenviar")}>Reenviar</button><button type="button" className="secundario" disabled={guardando} onClick={() => void accionInvitacion(invite, "revocar")}>Revocar</button></>}
          </div></td></tr>)}</tbody></table></div>}
          <p className="consultorio-admin__privacidad">El enlace de invitación se entrega por correo y nunca se muestra ni almacena en este panel.</p>
        </section>
      </div>}
    </div>
  </ProfesionalShell>;
}
