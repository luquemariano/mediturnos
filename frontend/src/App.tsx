import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";

import "./App.css";
import Dashboard from "./components/Dashboard";
import Disponibilidades from "./components/Disponibilidades";
import Especialidades from "./components/Especialidades";
import Pacientes from "./components/Pacientes";
import Prestaciones from "./components/Prestaciones";
import Profesionales from "./components/Profesionales";
import Turnos from "./components/Turnos";
import AgendaPropia from "./components/AgendaPropia";
import MiDisponibilidad from "./components/MiDisponibilidad";
import PerfilPropio from "./components/PerfilPropio";
import DashboardProfesional from "./components/DashboardProfesional";
import MisPrestaciones from "./components/MisPrestaciones";
import {
  iniciarSesion,
  obtenerUsuarioActual,
  restablecerPassword,
  solicitarRecuperacion,
} from "./services/authService";
import type { UsuarioActual } from "./types/auth";
import {
  EVENTO_SESION_NO_AUTORIZADA,
  habilitarNotificacionDeSesion,
} from "./api/manejoSesion";
import { restaurarSesion } from "./utils/sesion";


type Vista =
  | "dashboard"
  | "pacientes"
  | "especialidades"
  | "prestaciones"
  | "profesionales"
  | "turnos"
  | "disponibilidades"
  | "perfil";

type VistaAcceso = "login" | "forgot" | "reset";


function App() {
  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [mensaje, setMensaje] =
    useState("");

  const [cargando, setCargando] =
    useState(false);
  const [vistaAcceso, setVistaAcceso] = useState<VistaAcceso>(
    window.location.pathname === "/reset-password" ? "reset" : "login",
  );
  const [repetirPassword, setRepetirPassword] = useState("");

  const [usuario, setUsuario] =
    useState<UsuarioActual | null>(null);

  const [validandoSesion, setValidandoSesion] =
    useState(true);

  const [vista, setVista] =
    useState<Vista>("dashboard");


  useEffect(() => {
    let activo = true;

    function cerrarSesionPor401() {
      setUsuario(null);
      setVista("dashboard");
      setMensaje(
        "La sesión venció o no es válida. Iniciá sesión nuevamente.",
      );
    }

    window.addEventListener(
      EVENTO_SESION_NO_AUTORIZADA,
      cerrarSesionPor401,
    );

    void restaurarSesion(obtenerUsuarioActual).then(
      (usuarioRestaurado) => {
        if (activo) {
          setUsuario(usuarioRestaurado);
          setValidandoSesion(false);
        }
      },
    );

    return () => {
      activo = false;
      window.removeEventListener(
        EVENTO_SESION_NO_AUTORIZADA,
        cerrarSesionPor401,
      );
    };
  }, []);


  async function manejarInicioSesion(
    evento: FormEvent<HTMLFormElement>,
  ) {
    evento.preventDefault();

    setMensaje("");
    setCargando(true);

    try {
      const respuesta =
        await iniciarSesion({
          email,
          password,
        });

      localStorage.setItem(
        "access_token",
        respuesta.access_token,
      );
      habilitarNotificacionDeSesion();

      const usuarioActual =
        await obtenerUsuarioActual();

      setUsuario(usuarioActual);
      setVista("dashboard");
    } catch (error) {
      localStorage.removeItem("access_token");

      if (axios.isAxiosError(error)) {
        const detalle =
          error.response?.data?.detail;

        setMensaje(
          typeof detalle === "string"
            ? detalle
            : "No se pudo iniciar sesión.",
        );
      } else {
        setMensaje(
          "Ocurrió un error inesperado.",
        );
      }
    } finally {
      setCargando(false);
    }
  }

  async function manejarRecuperacion(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (cargando) return;
    setCargando(true);
    setMensaje("");
    try {
      const respuesta = await solicitarRecuperacion({ email });
      setMensaje(respuesta.mensaje);
    } catch {
      setMensaje("No pudimos enviar las instrucciones. Intentá nuevamente.");
    } finally {
      setCargando(false);
    }
  }

  async function manejarReset(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (cargando) return;
    if (password !== repetirPassword) {
      setMensaje("Las contraseñas no coinciden.");
      return;
    }
    const token = new URLSearchParams(window.location.search).get("token");
    if (!token) {
      setMensaje("El enlace de recuperación no es válido o venció.");
      return;
    }
    setCargando(true);
    setMensaje("");
    try {
      const respuesta = await restablecerPassword({ token, new_password: password });
      setMensaje(respuesta.mensaje);
    } catch (error) {
      const detalle = axios.isAxiosError(error) ? error.response?.data?.detail : null;
      setMensaje(typeof detalle === "string" ? detalle : "No pudimos actualizar tu contraseña.");
    } finally {
      setCargando(false);
    }
  }

  function volverAlLogin() {
    window.history.replaceState({}, "", "/");
    setVistaAcceso("login");
    setPassword("");
    setRepetirPassword("");
    setMensaje("");
  }


  if (validandoSesion) {
    return (
      <main className="pagina-login">
        <p>Validando sesión...</p>
      </main>
    );
  }


  function cerrarSesion() {
    localStorage.removeItem(
      "access_token",
    );

    setUsuario(null);
    setVista("dashboard");
    setPassword("");
    setMensaje("");
  }


  if (usuario) {
    if (vista === "dashboard" && usuario.rol === "profesional") {
      return (
        <DashboardProfesional
          nombre={usuario.nombre}
          onAbrirAgenda={() => setVista("turnos")}
          onAbrirPacientes={() => setVista("pacientes")}
          onAbrirDisponibilidad={() => setVista("disponibilidades")}
          onAbrirPrestaciones={() => setVista("prestaciones")}
          onAbrirPerfil={() => setVista("perfil")}
          onCerrarSesion={cerrarSesion}
        />
      );
    }

    if (vista === "pacientes") {
      return (
        <Pacientes
          nombre={usuario.nombre}
          onVolver={() =>
            setVista("dashboard")
          }
          onAbrirAgenda={() => setVista("turnos")}
          onAbrirDisponibilidad={() => setVista("disponibilidades")}
          onAbrirPrestaciones={() => setVista("prestaciones")}
          onAbrirPerfil={() => setVista("perfil")}
          onCerrarSesion={cerrarSesion}
        />
      );
    }

    if (vista === "turnos") {
      if (usuario.rol === "profesional" || usuario.rol === "paciente") {
        return <AgendaPropia
          tipo={usuario.rol}
          nombre={usuario.nombre}
          onVolver={() => setVista("dashboard")}
          onAbrirPacientes={() => setVista("pacientes")}
          onAbrirDisponibilidad={() => setVista("disponibilidades")}
          onAbrirPrestaciones={() => setVista("prestaciones")}
          onAbrirPerfil={() => setVista("perfil")}
          onCerrarSesion={cerrarSesion}
        />;
      }
      return (
        <Turnos
          rol={usuario.rol}
          onVolver={() =>
            setVista("dashboard")
          }
        />
      );
    }

    if (
      vista === "disponibilidades"
    ) {
      if (usuario.rol === "profesional") {
        return <MiDisponibilidad
          nombre={usuario.nombre}
          onVolver={() => setVista("dashboard")}
          onAbrirAgenda={() => setVista("turnos")}
          onAbrirPacientes={() => setVista("pacientes")}
          onAbrirPrestaciones={() => setVista("prestaciones")}
          onAbrirPerfil={() => setVista("perfil")}
          onCerrarSesion={cerrarSesion}
        />;
      }
      if (["administrador", "recepcionista"].includes(usuario.rol)) return (
        <Disponibilidades
          onVolver={() => setVista("dashboard")}
        />
      );
    }

    if (vista === "perfil" && usuario.rol === "profesional") {
      return <PerfilPropio
        tipo="profesional"
        nombre={usuario.nombre}
        onVolver={() => setVista("dashboard")}
        onAbrirAgenda={() => setVista("turnos")}
        onAbrirPacientes={() => setVista("pacientes")}
        onAbrirDisponibilidad={() => setVista("disponibilidades")}
        onAbrirPrestaciones={() => setVista("prestaciones")}
        onAbrirPerfil={() => setVista("perfil")}
        onCerrarSesion={cerrarSesion}
      />;
    }

    if (vista === "perfil" && usuario.rol === "paciente") {
      return <PerfilPropio tipo="paciente" onVolver={() => setVista("dashboard")} />;
    }

    if (vista === "profesionales") {
      return (
        <Profesionales
          rol={usuario.rol}
          onVolver={() =>
            setVista("dashboard")
          }
        />
      );
    }

    if (vista === "especialidades") {
      return (
        <Especialidades
          onVolver={() =>
            setVista("dashboard")
          }
        />
      );
    }

    if (vista === "prestaciones" && usuario.rol === "profesional") {
      return <MisPrestaciones
        nombre={usuario.nombre}
        onVolver={() => setVista("dashboard")}
        onAbrirAgenda={() => setVista("turnos")}
        onAbrirPacientes={() => setVista("pacientes")}
        onAbrirDisponibilidad={() => setVista("disponibilidades")}
        onAbrirPerfil={() => setVista("perfil")}
        onCerrarSesion={cerrarSesion}
      />;
    }

    if (
      vista === "prestaciones"
      && usuario.rol === "administrador"
    ) {
      return (
        <Prestaciones
          onVolver={() =>
            setVista("dashboard")
          }
        />
      );
    }

    return (
      <Dashboard
        nombre={usuario.nombre}
        rol={usuario.rol}
        onAbrirPacientes={() =>
          setVista("pacientes")
        }
        onAbrirProfesionales={() =>
          setVista("profesionales")
        }
        onAbrirEspecialidades={() =>
          setVista("especialidades")
        }
        onAbrirPrestaciones={() =>
          setVista("prestaciones")
        }
        onAbrirTurnos={() =>
          setVista("turnos")
        }
        onAbrirDisponibilidades={() =>
          setVista("disponibilidades")
        }
        onAbrirPerfil={() => setVista("perfil")}
        onCerrarSesion={cerrarSesion}
      />
    );
  }


  return (
    <main className="pagina-login">
      <section className="tarjeta-login">
        <div className="marca">
          <span className="marca-icono">
            +
          </span>

          <div>
            <h1>MediTurnos</h1>

            <p>
              Gestión médica simple y segura
            </p>
          </div>
        </div>

        {vistaAcceso === "forgot" && <form onSubmit={manejarRecuperacion}>
          <header className="acceso-encabezado">
            <h2>Recuperar contraseña</h2>
            <p>Ingresá tu correo y te enviaremos instrucciones.</p>
          </header>
          <div className="campo">
            <label htmlFor="email-recuperacion">Correo electrónico</label>
            <input id="email-recuperacion" type="email" value={email}
              onChange={(evento) => setEmail(evento.target.value)} required />
          </div>
          <button type="submit" disabled={cargando}>
            {cargando ? "Enviando…" : "Enviar instrucciones"}
          </button>
          {mensaje && <p className="mensaje-login" role="status">{mensaje}</p>}
          <button type="button" className="boton-enlace" onClick={volverAlLogin}>
            Volver a iniciar sesión
          </button>
        </form>}

        {vistaAcceso === "reset" && <form onSubmit={manejarReset}>
          <header className="acceso-encabezado">
            <h2>Restablecer contraseña</h2>
            <p>Elegí una nueva contraseña de al menos 8 caracteres.</p>
          </header>
          <div className="campo"><label htmlFor="new-password">Nueva contraseña</label>
            <input id="new-password" type="password" minLength={8} maxLength={128}
              value={password} onChange={(evento) => setPassword(evento.target.value)} required /></div>
          <div className="campo"><label htmlFor="repeat-password">Repetir contraseña</label>
            <input id="repeat-password" type="password" minLength={8} maxLength={128}
              value={repetirPassword} onChange={(evento) => setRepetirPassword(evento.target.value)} required /></div>
          <button type="submit" disabled={cargando}>{cargando ? "Guardando…" : "Actualizar contraseña"}</button>
          {mensaje && <p className="mensaje-login" role="status">{mensaje}</p>}
          <button type="button" className="boton-enlace" onClick={volverAlLogin}>Volver a iniciar sesión</button>
        </form>}

        {vistaAcceso === "login" && <form onSubmit={manejarInicioSesion}>
          <div className="campo">
            <label htmlFor="email">
              Correo electrónico
            </label>

            <input
              id="email"
              type="email"
              value={email}
              onChange={(evento) =>
                setEmail(
                  evento.target.value,
                )
              }
              placeholder={
                "usuario@mediturnos.com"
              }
              required
            />
          </div>

          <button type="button" className="boton-enlace olvide-password" onClick={() => {
            setVistaAcceso("forgot"); setMensaje("");
          }}>¿Olvidaste tu contraseña?</button>

          <div className="campo">
            <label htmlFor="password">
              Contraseña
            </label>

            <input
              id="password"
              type="password"
              value={password}
              onChange={(evento) =>
                setPassword(
                  evento.target.value,
                )
              }
              placeholder={
                "Ingresá tu contraseña"
              }
              required
            />
          </div>

          <button
            type="submit"
            disabled={cargando}
          >
            {cargando
              ? "Ingresando..."
              : "Iniciar sesión"}
          </button>

          {mensaje && (
            <p className="mensaje-login">
              {mensaje}
            </p>
          )}
        </form>}
      </section>
    </main>
  );
}

export default App;
