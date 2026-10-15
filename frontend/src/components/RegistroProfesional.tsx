import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";
import api from "../api/api";
import { registrarProfesional } from "../services/authService";
import { obtenerActividadesProfesionales } from "../services/actividadProfesionalService";
import { trackEvent } from "../analytics";
import type { Especialidad } from "../types/especialidad";
import type { ActividadProfesional } from "../types/profesional";
import type { RegistroProfesionalResponse } from "../types/auth";
import AuthBrand from "./AuthBrand";
import "./Onboarding.css";

type Formulario = {
  nombre: string;
  apellido: string;
  email: string;
  password: string;
  telefono: string;
  actividadId: string;
  matricula: string;
  especialidadId: string;
};

const inicial: Formulario = {
  nombre: "", apellido: "", email: "", password: "", telefono: "",
  actividadId: "", matricula: "", especialidadId: "",
};

export default function RegistroProfesional({ onRegistrado }: { onRegistrado: (r: RegistroProfesionalResponse) => void }) {
  const [actividades, setActividades] = useState<ActividadProfesional[]>([]);
  const [especialidades, setEspecialidades] = useState<Especialidad[]>([]);
  const [form, setForm] = useState<Formulario>(inicial);
  const [mensaje, setMensaje] = useState("");
  const [cargando, setCargando] = useState(false);
  const [cargandoCatalogo, setCargandoCatalogo] = useState(true);
  const actividad = useMemo(
    () => actividades.find((item) => item.id === Number(form.actividadId)),
    [actividades, form.actividadId],
  );

  useEffect(() => {
    let vigente = true;
    void Promise.all([
      obtenerActividadesProfesionales(),
      api.get<Especialidad[]>("/catalogo/especialidades").then((r) => r.data),
    ]).then(([catalogo, opciones]) => {
      if (!vigente) return;
      setActividades(catalogo);
      setEspecialidades(opciones);
    }).catch(() => {
      if (vigente) setMensaje("No pudimos cargar las actividades profesionales. Intentá nuevamente más tarde.");
    }).finally(() => { if (vigente) setCargandoCatalogo(false); });
    return () => { vigente = false; };
  }, []);

  function cambiar(campo: keyof Formulario, valor: string) {
    setForm((actual) => campo === "actividadId"
      ? { ...actual, actividadId: valor, matricula: "", especialidadId: "" }
      : { ...actual, [campo]: valor });
    setMensaje("");
  }

  async function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (!actividad) {
      setMensaje("Seleccioná una actividad profesional.");
      return;
    }
    trackEvent("sign_up_start");
    setCargando(true);
    setMensaje("");
    const datos = {
      nombre: form.nombre,
      apellido: form.apellido,
      email: form.email,
      password: form.password,
      ...(form.telefono ? { telefono: form.telefono } : {}),
      actividad_profesional_id: actividad.id,
      ...(actividad.requiere_matricula ? { matricula: form.matricula } : {}),
      ...(actividad.requiere_especialidad ? { especialidad_id: Number(form.especialidadId) } : {}),
    };
    try {
      const respuesta = await registrarProfesional(datos);
      onRegistrado(respuesta);
    } catch (error) {
      const detalle = axios.isAxiosError(error) ? error.response?.data?.detail : null;
      setMensaje(typeof detalle === "string" ? detalle : "No pudimos crear tu cuenta.");
    } finally {
      setCargando(false);
    }
  }

  return <main className="pagina-onboarding"><div className="onboarding-acceso"><AuthBrand subtitulo="Empezá a organizar tu consulta"/><form className="onboarding-card onboarding-form" onSubmit={enviar}>
    <header><p className="acceso-etiqueta">Cuenta profesional</p><h1>Creá tu cuenta</h1><p>Completá tus datos para empezar.</p></header>
    <div className="onboarding-grid">
      <label>Nombre<input value={form.nombre} onChange={(e) => cambiar("nombre", e.target.value)} minLength={2} maxLength={100} required/></label>
      <label>Apellido<input value={form.apellido} onChange={(e) => cambiar("apellido", e.target.value)} minLength={2} maxLength={100} required/></label>
      <label className="ancho-completo">Correo electrónico<input type="email" value={form.email} onChange={(e) => cambiar("email", e.target.value)} required/></label>
      <label>Contraseña<input type="password" value={form.password} onChange={(e) => cambiar("password", e.target.value)} minLength={8} maxLength={128} required/><small>Mínimo 8 caracteres.</small></label>
      <label>Teléfono (opcional)<input value={form.telefono} onChange={(e) => cambiar("telefono", e.target.value)} maxLength={30}/></label>
      <label className="ancho-completo">Actividad profesional
        <select value={form.actividadId} onChange={(e) => cambiar("actividadId", e.target.value)} required disabled={cargandoCatalogo || cargando}>
          <option value="">{cargandoCatalogo ? "Cargando actividades…" : "Seleccioná tu actividad"}</option>
          {actividades.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}
        </select>
      </label>
      {actividad?.requiere_matricula && <label>Matrícula *
        <input value={form.matricula} onChange={(e) => cambiar("matricula", e.target.value)} minLength={3} maxLength={50} required aria-describedby="registro-matricula-ayuda"/>
        <small id="registro-matricula-ayuda">Ingresá la matrícula correspondiente a tu actividad.</small>
      </label>}
      {actividad?.requiere_especialidad && <label>Profesión / especialidad *
        <select value={form.especialidadId} onChange={(e) => cambiar("especialidadId", e.target.value)} required>
          <option value="">Seleccioná una opción</option>{especialidades.map((item) => <option key={item.id} value={item.id}>{item.nombre}</option>)}
        </select>
      </label>}
      {actividad && !actividad.requiere_matricula && <p className="ancho-completo" role="status">Esta actividad no requiere matrícula para usar la agenda y gestionar turnos.</p>}
    </div>
    {mensaje&&<p className="onboarding-error" role="alert">{mensaje}</p>}
    <button disabled={cargando || cargandoCatalogo}>{cargando ? "Creando cuenta…" : "Crear cuenta"}</button>
    <a className="onboarding-link" href="/login">Ya tengo una cuenta</a>
  </form></div></main>;
}
