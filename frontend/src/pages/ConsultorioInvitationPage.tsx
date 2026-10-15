import { useState, type FormEvent } from "react";
import api from "../api/api";
import { iniciarSesion, obtenerUsuarioActual } from "../services/authService";
import type { UsuarioActual } from "../types/auth";

type Props = { usuario: UsuarioActual | null; onAutenticado: (usuario: UsuarioActual) => void };

export default function ConsultorioInvitationPage({ usuario, onAutenticado }: Props) {
  const [token] = useState(() => new URLSearchParams(window.location.hash.slice(1)).get("token") ?? "");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [cargando, setCargando] = useState(false);

  async function aceptar(force = false) {
    if (!token || (cargando && !force)) return;
    setCargando(true); setMensaje("");
    try {
      await api.post("/consultorios/aceptar-invitacion", { token });
      window.history.replaceState({}, "", "/invitacion-consultorio");
      setMensaje("La invitación fue aceptada. Tus módulos autorizados ya están asociados a tu perfil profesional.");
    } catch {
      setMensaje("No pudimos aceptar esta invitación. Verificá que hayas iniciado sesión con el correo invitado y que el enlace siga vigente.");
    } finally { setCargando(false); }
  }

  async function ingresar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setCargando(true); setMensaje("");
    try {
      const session = await iniciarSesion({ email, password });
      localStorage.setItem("access_token", session.access_token);
      const current = await obtenerUsuarioActual();
      onAutenticado(current);
      await aceptar(true);
    } catch {
      setMensaje("No pudimos iniciar sesión. Revisá tus datos y que el correo esté verificado.");
    } finally { setCargando(false); }
  }

  return <main className="pagina-login"><div className="acceso-publico">
    <section className="tarjeta-login" aria-labelledby="invitacion-titulo">
      <header className="acceso-encabezado"><p className="acceso-etiqueta">Turnelia</p><h2 id="invitacion-titulo">Invitación a un consultorio</h2></header>
      {!token ? <p role="alert">El enlace no es válido o ya no está disponible.</p> : usuario ? <>
        <p>Iniciaste sesión como <strong>{usuario.email}</strong>. Aceptá con esta cuenta profesional.</p>
        {mensaje && <p role="status">{mensaje}</p>}
        {!mensaje.startsWith("La invitación fue aceptada") && <button type="button" disabled={cargando} onClick={() => void aceptar()}>{cargando ? "Procesando…" : "Aceptar invitación"}</button>}
      </> : <>
        <p>Ingresá con la cuenta profesional que recibió la invitación.</p>
        <form className="formulario-acceso" onSubmit={(event) => void ingresar(event)}>
          <div className="campo"><label htmlFor="invite-email">Correo electrónico</label><input id="invite-email" type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} /></div>
          <div className="campo"><label htmlFor="invite-password">Contraseña</label><input id="invite-password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} /></div>
          {mensaje && <p className="mensaje-login mensaje-error" role="alert">{mensaje}</p>}
          <button type="submit" disabled={cargando}>{cargando ? "Ingresando…" : "Iniciar sesión y aceptar"}</button>
        </form>
        <p>¿Todavía no tenés cuenta? <a href="/registro" target="_blank" rel="noreferrer">Creá tu cuenta profesional en otra pestaña</a>, verificá el correo y luego volvé aquí para aceptar.</p>
      </>}
      <a href="/login">Volver al inicio de sesión</a>
    </section></div>
  </main>;
}
