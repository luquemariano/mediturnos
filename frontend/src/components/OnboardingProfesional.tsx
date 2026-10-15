import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";
import { avanzarOnboarding, completarOnboarding, obtenerOnboarding } from "../services/onboardingService";
import { actualizarMiPerfil } from "../services/profesionalService";
import { obtenerActividadesProfesionales } from "../services/actividadProfesionalService";
import { obtenerEspecialidades } from "../services/especialidadService";
import { crearMiPrestacion, obtenerMisPrestaciones } from "../services/prestacionService";
import { crearMiDisponibilidad, obtenerMisDisponibilidades } from "../services/disponibilidadService";
import type { OnboardingStep } from "../types/auth";
import type { OnboardingEstado } from "../types/onboarding";
import type { Prestacion } from "../types/prestacion";
import type { Disponibilidad } from "../types/disponibilidad";
import type { ActividadProfesional } from "../types/profesional";
import type { Especialidad } from "../types/especialidad";
import "./Onboarding.css";
import { rutaOnboarding } from "../utils/onboarding";
import { capturePostHogEvent } from "../posthog";

const DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

type PerfilFormulario = {
  nombre: string;
  apellido: string;
  telefono: string;
  email: string;
  actividadId: string;
  matricula: string;
  especialidadId: string;
};

const perfilInicial: PerfilFormulario = {
  nombre: "", apellido: "", telefono: "", email: "", actividadId: "", matricula: "", especialidadId: "",
};

export default function OnboardingProfesional({ pasoRuta, onNavegar, onCompletado }: { pasoRuta: OnboardingStep; onNavegar: (ruta: string) => void; onCompletado: () => void }) {
  const [estado, setEstado] = useState<OnboardingEstado | null>(null);
  const [mensaje, setMensaje] = useState("");
  const [cargando, setCargando] = useState(true);
  const [prestaciones, setPrestaciones] = useState<Prestacion[]>([]);
  const [disponibilidades, setDisponibilidades] = useState<Disponibilidad[]>([]);
  const [actividades, setActividades] = useState<ActividadProfesional[]>([]);
  const [especialidades, setEspecialidades] = useState<Especialidad[]>([]);
  const [perfil, setPerfil] = useState<PerfilFormulario>(perfilInicial);
  const [prestacion, setPrestacion] = useState({ nombre: "", duracion_minutos: "30", precio: "", modalidad: "presencial" as "presencial" | "virtual" });
  const [horario, setHorario] = useState({ dia_semana: "0", hora_inicio: "09:00", hora_fin: "13:00" });

  const actividad = useMemo(
    () => actividades.find((item) => item.id === Number(perfil.actividadId)),
    [actividades, perfil.actividadId],
  );

  useEffect(() => {
    let vigente = true;
    void Promise.all([
      obtenerOnboarding(),
      obtenerActividadesProfesionales(),
      obtenerEspecialidades(),
      obtenerMisPrestaciones(),
      obtenerMisDisponibilidades(),
    ]).then(([onboarding, catalogo, catalogoEspecialidades, p, d]) => {
      if (!vigente) return;
      if (onboarding.onboarding_step === "completado") {
        onCompletado();
        return;
      }
      setEstado(onboarding);
      setActividades(catalogo);
      setEspecialidades(catalogoEspecialidades);
      setPrestaciones(p);
      setDisponibilidades(d);
      setPerfil({
        nombre: onboarding.perfil.nombre,
        apellido: onboarding.perfil.apellido,
        telefono: onboarding.perfil.telefono ?? "",
        email: onboarding.perfil.email ?? "",
        actividadId: onboarding.perfil.actividad_profesional_id?.toString() ?? "",
        matricula: onboarding.perfil.matricula ?? "",
        especialidadId: onboarding.perfil.especialidades[0]?.especialidad_id.toString() ?? "",
      });
      if (rutaOnboarding(onboarding.onboarding_step) !== window.location.pathname) {
        onNavegar(rutaOnboarding(onboarding.onboarding_step));
      }
    }).catch(() => setMensaje("No pudimos cargar tu onboarding.")).finally(() => setCargando(false));
    return () => { vigente = false; };
  }, [onCompletado, onNavegar]);

  async function avanzar(siguiente: OnboardingStep) {
    setCargando(true); setMensaje("");
    try {
      const nuevo = await avanzarOnboarding(siguiente);
      setEstado(nuevo);
      onNavegar(rutaOnboarding(nuevo.onboarding_step));
    } catch (error) { setMensaje(errorTexto(error)); }
    finally { setCargando(false); }
  }

  async function guardarPerfil(evento: FormEvent) {
    evento.preventDefault(); setCargando(true); setMensaje("");
    try {
      const cambios: Parameters<typeof actualizarMiPerfil>[0] = {
        nombre: perfil.nombre,
        apellido: perfil.apellido,
        telefono: perfil.telefono || null,
        email: perfil.email || null,
      };
      if (actividad) {
        cambios.actividad_profesional_id = actividad.id;
        if (actividad.requiere_matricula) cambios.matricula = perfil.matricula;
        else if (estado?.perfil.actividad_profesional_id !== actividad.id || estado.perfil.matricula) cambios.matricula = null;
        const especialidadOriginal = estado?.perfil.especialidades[0]?.especialidad_id;
        if (actividad.requiere_especialidad && (
          actividad.id !== estado?.perfil.actividad_profesional_id
          || Number(perfil.especialidadId) !== especialidadOriginal
        )) {
          cambios.especialidades = [{
            especialidad_id: Number(perfil.especialidadId),
            duracion_turno_minutos: especialidades.find((item) => item.id === Number(perfil.especialidadId))?.duracion_turno_minutos ?? 30,
          }];
        }
      }
      await actualizarMiPerfil(cambios);
      await avanzar("prestaciones");
    } catch (error) { setMensaje(errorTexto(error)); setCargando(false); }
  }

  async function agregarPrestacion(evento: FormEvent) {
    evento.preventDefault(); if (!estado) return; setCargando(true);
    try {
      const nueva = await crearMiPrestacion({ nombre: prestacion.nombre, duracion_minutos: Number(prestacion.duracion_minutos), precio: Number(prestacion.precio), modalidad: prestacion.modalidad, especialidad_id: estado.perfil.especialidades[0].especialidad_id });
      capturePostHogEvent("prestation_created", { source: "onboarding", modalidad: prestacion.modalidad, duracion: String(Number(prestacion.duracion_minutos)) });
      setPrestaciones((anteriores) => [...anteriores, nueva]); setPrestacion((actual) => ({ ...actual, nombre: "", precio: "" }));
    } catch (error) { setMensaje(errorTexto(error)); }
    finally { setCargando(false); }
  }

  async function agregarHorario(evento: FormEvent) {
    evento.preventDefault(); setCargando(true);
    try {
      const nuevo = await crearMiDisponibilidad({ dia_semana: Number(horario.dia_semana), hora_inicio: horario.hora_inicio, hora_fin: horario.hora_fin });
      capturePostHogEvent("availability_created", { source: "onboarding" }); setDisponibilidades((anteriores) => [...anteriores, nuevo]);
    } catch (error) { setMensaje(errorTexto(error)); }
    finally { setCargando(false); }
  }

  async function finalizar() {
    setCargando(true);
    try { await completarOnboarding(); capturePostHogEvent("onboarding_completed", { source: "onboarding" }); onCompletado(); }
    catch (error) { setMensaje(errorTexto(error)); setCargando(false); }
  }

  if (cargando && !estado) return <main className="pagina-onboarding"><p>Preparando tu cuenta…</p></main>;
  return <main className="pagina-onboarding"><section className="onboarding-shell">
    <header className="onboarding-top"><img src="/brand/mediturnos-logo-horizontal.svg" alt="Turnelia"/><span>Paso {Math.min(["perfil", "prestaciones", "disponibilidad", "listo"].indexOf(pasoRuta) + 1, 4)} de 4</span></header>
    <div className="onboarding-card">
      {pasoRuta === "perfil" && <form className="onboarding-form" onSubmit={guardarPerfil}>
        <h1>Revisá tu perfil</h1><p>Estos datos identifican tu actividad profesional.</p>
        <div className="onboarding-grid">
          <label>Nombre<input value={perfil.nombre} onChange={(e) => setPerfil({ ...perfil, nombre: e.target.value })} required/></label>
          <label>Apellido<input value={perfil.apellido} onChange={(e) => setPerfil({ ...perfil, apellido: e.target.value })} required/></label>
          <label className="ancho-completo">Actividad profesional
            <select value={perfil.actividadId} onChange={(e) => setPerfil({ ...perfil, actividadId: e.target.value, matricula: "", especialidadId: "" })}>
              <option value="">Sin clasificar</option>{actividades.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}
            </select>
            {!estado?.perfil.actividad_profesional_id && <small>Si ya tenías una cuenta, podés completar esta clasificación ahora o conservar el perfil sin clasificar.</small>}
          </label>
          {actividad?.requiere_matricula && <label>Matrícula *<input value={perfil.matricula} onChange={(e) => setPerfil({ ...perfil, matricula: e.target.value })} minLength={3} maxLength={50} required/></label>}
          {actividad?.requiere_especialidad && <label>Profesión / especialidad *
            <select value={perfil.especialidadId} onChange={(e) => setPerfil({ ...perfil, especialidadId: e.target.value })} required>
              <option value="">Seleccioná una opción</option>{especialidades.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}
            </select>
          </label>}
          {actividad && !actividad.requiere_matricula && <p className="ancho-completo" role="status">Esta actividad no requiere matrícula.</p>}
          <label>Teléfono<input value={perfil.telefono} onChange={(e) => setPerfil({ ...perfil, telefono: e.target.value })}/></label>
          <label className="ancho-completo">Email de contacto<input type="email" value={perfil.email} onChange={(e) => setPerfil({ ...perfil, email: e.target.value })}/></label>
        </div>
        <button disabled={cargando}>Continuar</button>
      </form>}
      {pasoRuta === "prestaciones" && <div><h1>Configurá tus prestaciones</h1><p>Podés cargar ahora los servicios que ofrecés o hacerlo más adelante desde Mis prestaciones.</p>
        <form className="onboarding-inline" onSubmit={agregarPrestacion}><input aria-label="Nombre de la prestación" placeholder="Ej. Consulta inicial" value={prestacion.nombre} onChange={(e) => setPrestacion({ ...prestacion, nombre: e.target.value })} required/><input aria-label="Duración" type="number" min="10" max="240" value={prestacion.duracion_minutos} onChange={(e) => setPrestacion({ ...prestacion, duracion_minutos: e.target.value })}/><input aria-label="Precio" type="number" min="0" step="0.01" placeholder="Precio" value={prestacion.precio} onChange={(e) => setPrestacion({ ...prestacion, precio: e.target.value })} required/><button disabled={cargando}>Agregar prestación</button></form>
        <ul className="onboarding-lista">{prestaciones.map((item) => <li key={item.id}><strong>{item.nombre}</strong><span>{item.duracion_minutos} min · ${item.precio}</span></li>)}</ul><Acciones onContinuar={() => avanzar("disponibilidad")} cargando={cargando}/>
      </div>}
      {pasoRuta === "disponibilidad" && <div><h1>Configurá tus horarios de atención</h1><p>Podés hacerlo ahora o más adelante desde Mi disponibilidad. Tus horarios se pueden modificar cuando quieras.</p>
        <form className="onboarding-inline" onSubmit={agregarHorario}><select aria-label="Día" value={horario.dia_semana} onChange={(e) => setHorario({ ...horario, dia_semana: e.target.value })}>{DIAS.map((dia, i) => <option value={i} key={dia}>{dia}</option>)}</select><input aria-label="Hora de inicio" type="time" value={horario.hora_inicio} onChange={(e) => setHorario({ ...horario, hora_inicio: e.target.value })}/><input aria-label="Hora de fin" type="time" value={horario.hora_fin} onChange={(e) => setHorario({ ...horario, hora_fin: e.target.value })}/><button disabled={cargando}>Agregar horario</button></form>
        <ul className="onboarding-lista">{disponibilidades.map((item) => <li key={item.id}><strong>{DIAS[item.dia_semana]}</strong><span>{item.hora_inicio.slice(0, 5)} a {item.hora_fin.slice(0, 5)}</span></li>)}</ul><Acciones onContinuar={() => avanzar("listo")} cargando={cargando}/>
      </div>}
      {pasoRuta === "listo" && <div className="onboarding-listo"><span aria-hidden="true">✓</span><h1>Tu cuenta está lista</h1><p>Ya podés empezar a gestionar tu consulta con Turnelia.</p><button onClick={finalizar} disabled={cargando}>Ir a mi panel</button></div>}
      {mensaje && <p className="onboarding-error" role="alert">{mensaje}</p>}
    </div>
  </section></main>;
}

function Acciones({ onContinuar, cargando }: { onContinuar: () => void; cargando: boolean }) {
  return <div className="onboarding-acciones"><button onClick={onContinuar} disabled={cargando}>Continuar</button><button className="boton-omitir" onClick={onContinuar} disabled={cargando}>Omitir por ahora</button></div>;
}

function errorTexto(error: unknown) {
  const detalle = axios.isAxiosError(error) ? error.response?.data?.detail : null;
  return typeof detalle === "string" ? detalle : "No pudimos guardar los cambios.";
}
