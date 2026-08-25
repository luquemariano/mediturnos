import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";
import api from "../api/api";
import { registrarProfesional } from "../services/authService";
import type { Especialidad } from "../types/especialidad";
import type { RegistroProfesionalResponse } from "../types/auth";
import AuthBrand from "./AuthBrand";
import "./Onboarding.css";

export default function RegistroProfesional({ onRegistrado }: { onRegistrado: (r: RegistroProfesionalResponse) => void }) {
  const [especialidades, setEspecialidades] = useState<Especialidad[]>([]);
  const [form, setForm] = useState({ nombre: "", apellido: "", email: "", password: "", telefono: "", matricula: "", especialidad_id: "" });
  const [mensaje, setMensaje] = useState(""); const [cargando, setCargando] = useState(false);
  useEffect(() => { void api.get<Especialidad[]>("/catalogo/especialidades").then(r => setEspecialidades(r.data)).catch(() => setMensaje("No pudimos cargar las profesiones y especialidades.")); }, []);
  const campo = (nombre: keyof typeof form, valor: string) => setForm(actual => ({ ...actual, [nombre]: valor }));
  async function enviar(e: FormEvent) { e.preventDefault(); setCargando(true); setMensaje(""); try { const respuesta = await registrarProfesional({ ...form, telefono: form.telefono || undefined, especialidad_id: Number(form.especialidad_id) }); onRegistrado(respuesta); } catch (error) { const detalle = axios.isAxiosError(error) ? error.response?.data?.detail : null; setMensaje(typeof detalle === "string" ? detalle : "No pudimos crear tu cuenta."); } finally { setCargando(false); } }
  return <main className="pagina-onboarding"><div className="onboarding-acceso"><AuthBrand subtitulo="Empezá a organizar tu consulta"/><form className="onboarding-card onboarding-form" onSubmit={enviar}><header><p className="acceso-etiqueta">Cuenta profesional</p><h1>Creá tu cuenta</h1><p>Completá tus datos para empezar.</p></header><div className="onboarding-grid">
    <label>Nombre<input value={form.nombre} onChange={e=>campo("nombre",e.target.value)} minLength={2} maxLength={100} required/></label><label>Apellido<input value={form.apellido} onChange={e=>campo("apellido",e.target.value)} minLength={2} maxLength={100} required/></label>
    <label className="ancho-completo">Correo electrónico<input type="email" value={form.email} onChange={e=>campo("email",e.target.value)} required/></label><label>Contraseña<input type="password" value={form.password} onChange={e=>campo("password",e.target.value)} minLength={8} maxLength={128} required/><small>Mínimo 8 caracteres.</small></label><label>Teléfono (opcional)<input value={form.telefono} onChange={e=>campo("telefono",e.target.value)} maxLength={30}/></label>
    <label>Matrícula<input value={form.matricula} onChange={e=>campo("matricula",e.target.value)} minLength={3} maxLength={50} required/></label><label>Profesión / especialidad<select value={form.especialidad_id} onChange={e=>campo("especialidad_id",e.target.value)} required><option value="">Seleccioná una opción</option>{especialidades.map(x=><option key={x.id} value={x.id}>{x.nombre}</option>)}</select></label>
  </div>{mensaje&&<p className="onboarding-error" role="alert">{mensaje}</p>}<button disabled={cargando}>{cargando?"Creando cuenta…":"Crear cuenta"}</button><a className="onboarding-link" href="/login">Ya tengo una cuenta</a></form></div></main>;
}
