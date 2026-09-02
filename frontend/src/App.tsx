import { useCallback, useEffect, useState } from "react";
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
import AuthBrand from "./components/AuthBrand";
import DashboardProfesional from "./components/DashboardProfesional";
import MisPrestaciones from "./components/MisPrestaciones";
import "./responsiveAudit.css";
import LandingPage from "./landing/LandingPage";
import RegistroProfesional from "./components/RegistroProfesional";
import OnboardingProfesional from "./components/OnboardingProfesional";
import CuentasAdmin from "./components/CuentasAdmin";
import ActivarSuscripcion from "./components/ActivarSuscripcion";
import RetornoSuscripcion from "./components/RetornoSuscripcion";
import StudyUploadAccess from "./pages/StudyUploadAccess";
import { rutaOnboarding } from "./utils/onboarding";
import { debeForzarOnboarding } from "./utils/rutasPublicas";
import {
  iniciarSesion,
  obtenerUsuarioActual,
  restablecerPassword,
  solicitarRecuperacion,
} from "./services/authService";
import { obtenerOnboarding } from "./services/onboardingService";
import type { RegistroProfesionalResponse, OnboardingStep } from "./types/auth";
import type { UsuarioActual } from "./types/auth";
import {
  EVENTO_SESION_NO_AUTORIZADA,
  habilitarNotificacionDeSesion,
} from "./api/manejoSesion";
import { restaurarSesion } from "./utils/sesion";
import { aplicarMetadatosSeo } from "./seo/routeMetadata";
import BootLoadingScreen, { type BootStep } from "./components/BootLoadingScreen";
import { HelpArticlePage, HelpHome, HelpLayout } from "./help";
import { trackEvent, trackPageView } from "./analytics";


type Vista =
  | "dashboard"
  | "pacientes"
  | "especialidades"
  | "prestaciones"
  | "profesionales"
  | "turnos"
  | "disponibilidades"
  | "perfil"
  | "cuentas";

type VistaAcceso = "login" | "forgot" | "reset";

const UMBRAL_LOADER_MS = 600;
const UMBRAL_ESPERA_PROLONGADA_MS = 7000;


function App() {
  const rutaInicial = window.location.pathname;
  const [ruta, setRuta] = useState(rutaInicial);
  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [mensaje, setMensaje] =
    useState("");

  const [cargando, setCargando] =
    useState(false);
  const [vistaAcceso, setVistaAcceso] = useState<VistaAcceso>(
    rutaInicial === "/reset-password" ? "reset" : rutaInicial === "/forgot-password" ? "forgot" : "login",
  );
  const [repetirPassword, setRepetirPassword] = useState("");

  const [usuario, setUsuario] =
    useState<UsuarioActual | null>(null);

  const [validandoSesion, setValidandoSesion] =
    useState(true);
  const [bootSteps, setBootSteps] = useState<BootStep[]>([]);
  const [bootActivo, setBootActivo] = useState(false);
  const [bootVisible, setBootVisible] = useState(false);
  const [bootProlongado, setBootProlongado] = useState(false);

  const [vista, setVista] =
    useState<Vista>("dashboard");
  const [pacienteIdInicial, setPacienteIdInicial] = useState<number | undefined>();
  const [studyRequestIdInicial, setStudyRequestIdInicial] = useState<number | undefined>();

  useEffect(() => {
    if (!bootActivo) { setBootVisible(false); setBootProlongado(false); return; }
    const visible = window.setTimeout(() => setBootVisible(true), UMBRAL_LOADER_MS);
    const prolonged = window.setTimeout(() => setBootProlongado(true), UMBRAL_ESPERA_PROLONGADA_MS);
    return () => { window.clearTimeout(visible); window.clearTimeout(prolonged); };
  }, [bootActivo]);

  function iniciarBoot(labels: string[]) {
    setBootSteps(labels.map((label, index) => ({ id: String(index), label, status: index === 0 ? "loading" : "pending" })));
    setBootActivo(true);
  }

  function completarBoot(id: string) {
    setBootSteps((actuales) => {
      const indice = actuales.findIndex((paso) => paso.id === id);
      return actuales.map((paso, posicion) => posicion === indice ? { ...paso, status: "complete" } : posicion === indice + 1 ? { ...paso, status: "loading" } : paso);
    });
  }

  useEffect(() => {
    aplicarMetadatosSeo(window.location.pathname);
    trackPageView(window.location.pathname);
  }, [ruta, vistaAcceso]);

  const navegar = useCallback((destino: string) => {
    if (window.location.pathname !== destino) window.history.pushState({}, "", destino);
    setRuta(destino);
  }, []);

  const abrirDashboard = useCallback(() => { navegar("/app"); setVista("dashboard"); }, [navegar]);

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

    const manejarPopState = () => setRuta(window.location.pathname);
    window.addEventListener("popstate", manejarPopState);
    if (localStorage.getItem("access_token")) iniciarBoot(["Validando tu cuenta"]);
    void restaurarSesion(obtenerUsuarioActual).then(
      async (usuarioRestaurado) => {
        if (activo) {
          if (usuarioRestaurado) completarBoot("0");
          setUsuario(usuarioRestaurado);
          if (usuarioRestaurado?.rol === "profesional") {
            try {
              setBootSteps((actuales) => [...actuales, { id: "1", label: "Preparando tu espacio", status: "loading" }]);
              const estado = await obtenerOnboarding();
              completarBoot("1");
              if (estado.onboarding_step !== "completado" && debeForzarOnboarding(window.location.pathname)) {
                navegar(rutaOnboarding(estado.onboarding_step));
              }
            } catch { /* La sesión global manejará un eventual 401. */ }
          }
          setValidandoSesion(false);
          setBootActivo(false);
        }
      },
    );

    return () => {
      activo = false;
      window.removeEventListener(
        EVENTO_SESION_NO_AUTORIZADA,
        cerrarSesionPor401,
      );
      window.removeEventListener("popstate", manejarPopState);
    };
  }, [navegar]);

  useEffect(() => {
    if (usuario && usuario.rol !== "profesional" && ruta.startsWith("/onboarding/")) navegar("/app");
  }, [navegar, ruta, usuario]);


  async function manejarInicioSesion(
    evento: FormEvent<HTMLFormElement>,
  ) {
    evento.preventDefault();

    setMensaje("");
    setCargando(true);
    iniciarBoot(["Iniciando sesión", "Validando tu cuenta"]);

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
      completarBoot("0");

      const usuarioActual =
        await obtenerUsuarioActual();
      completarBoot("1");

      setUsuario(usuarioActual);
      trackEvent("login_success");
      setVista("dashboard");
      if (usuarioActual.rol === "profesional") {
        setBootSteps((actuales) => [...actuales, { id: "2", label: "Preparando tu espacio", status: "loading" }]);
        const estado = await obtenerOnboarding();
        completarBoot("2");
        navegar(estado.onboarding_step === "completado" ? "/app" : rutaOnboarding(estado.onboarding_step));
      } else navegar("/app");
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
      setBootActivo(false);
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
    window.history.replaceState({}, "", "/login");
    setRuta("/login");
    setVistaAcceso("login");
    setPassword("");
    setRepetirPassword("");
    setMensaje("");
  }


  if (ruta === "/") {
    return <LandingPage />;
  }

  if (ruta === "/estudios/enviar") return <StudyUploadAccess />;

  if (ruta === "/ayuda" || ruta.startsWith("/ayuda/")) {
    const slug = ruta.slice("/ayuda/".length);
    return <HelpLayout onHome={() => navegar("/ayuda")} onLogin={() => navegar(usuario ? "/app" : "/login")} loggedIn={Boolean(usuario)}>
      {ruta === "/ayuda" ? <HelpHome onOpenArticle={(articleSlug) => navegar(`/ayuda/${articleSlug}`)} /> : <HelpArticlePage slug={slug} onHome={() => navegar("/ayuda")} onOpenArticle={(articleSlug) => navegar(`/ayuda/${articleSlug}`)} />}
    </HelpLayout>;
  }

  if (ruta === "/suscripcion/retorno") {
    return <RetornoSuscripcion
      autenticada={Boolean(usuario)}
      onIngresar={() => { setVistaAcceso("login"); navegar("/login"); }}
      onVolver={() => navegar("/app/suscripcion")}
    />;
  }

  if (validandoSesion) {
    if (bootActivo && bootVisible) return <BootLoadingScreen steps={bootSteps} prolonged={bootProlongado} />;
    return (
      <main className="pagina-login">
        <p>Validando sesión...</p>
      </main>
    );
  }

  if (bootActivo && bootVisible) return <BootLoadingScreen steps={bootSteps} prolonged={bootProlongado} />;


  function cerrarSesion() {
    localStorage.removeItem(
      "access_token",
    );

    setUsuario(null);
    setVista("dashboard");
    setPassword("");
    setMensaje("");
    navegar("/login");
  }

  async function manejarRegistroExitoso(respuesta: RegistroProfesionalResponse) {
    localStorage.setItem("access_token", respuesta.access_token);
    habilitarNotificacionDeSesion();
    trackEvent("sign_up_complete");
    setUsuario(await obtenerUsuarioActual());
    navegar("/onboarding/perfil");
  }

  const pasoRuta = ruta.startsWith("/onboarding/") ? ruta.split("/").pop() as OnboardingStep : null;

  if (!usuario && ruta === "/registro") return <RegistroProfesional onRegistrado={manejarRegistroExitoso}/>;

  if (usuario && usuario.rol === "profesional" && pasoRuta && ["perfil","prestaciones","disponibilidad","listo"].includes(pasoRuta)) {
    return <OnboardingProfesional pasoRuta={pasoRuta} onNavegar={navegar} onCompletado={abrirDashboard}/>;
  }

  if (usuario && ruta.startsWith("/onboarding/")) return <main className="pagina-login"><p>Redirigiendo…</p></main>;


  if (usuario) {
    if (ruta === "/app/suscripcion") {
      return <ActivarSuscripcion onVolver={abrirDashboard} />;
    }
    if (vista === "dashboard" && usuario.rol === "profesional") {
      return (
        <DashboardProfesional
          nombre={usuario.nombre}
          onAbrirAgenda={() => setVista("turnos")}
          onAbrirPacientes={(patientId, studyRequestId) => { setPacienteIdInicial(patientId); setStudyRequestIdInicial(studyRequestId); setVista("pacientes"); }}
          onAbrirDisponibilidad={() => setVista("disponibilidades")}
          onAbrirPrestaciones={() => setVista("prestaciones")}
          onAbrirPerfil={() => setVista("perfil")}
          onAbrirSuscripcion={() => navegar("/app/suscripcion")}
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
          pacienteIdInicial={pacienteIdInicial}
          studyRequestIdInicial={studyRequestIdInicial}
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

    if (vista === "cuentas" && usuario.rol === "administrador") {
      return <CuentasAdmin onVolver={() => setVista("dashboard")} />;
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
        onAbrirCuentas={() => setVista("cuentas")}
        onCerrarSesion={cerrarSesion}
      />
    );
  }


  return (
    <main className="pagina-login">
      <div className="acceso-publico">
        <AuthBrand subtitulo="Agenda profesional" />

        <section className="tarjeta-login">
        {vistaAcceso === "forgot" && <form className="formulario-acceso" onSubmit={manejarRecuperacion}>
          <header className="acceso-encabezado">
            <p className="acceso-etiqueta">Seguridad de tu cuenta</p>
            <h2>Recuperar acceso</h2>
            <p>Te enviaremos instrucciones para crear una nueva contraseña.</p>
          </header>
          <div className="campo">
            <label htmlFor="email-recuperacion">Correo electrónico</label>
            <input id="email-recuperacion" type="email" value={email}
              onChange={(evento) => setEmail(evento.target.value)} required />
          </div>
          <button type="submit" disabled={cargando}>
            {cargando ? "Enviando…" : "Enviar instrucciones"}
          </button>
          {mensaje && <p className={`mensaje-login ${mensaje.startsWith("No pudimos") ? "mensaje-error" : "mensaje-exito"}`} role="status">{mensaje}</p>}
          <button type="button" className="boton-secundario" onClick={volverAlLogin}>
            Volver al inicio de sesión
          </button>
        </form>}

        {vistaAcceso === "reset" && <form className="formulario-acceso" onSubmit={manejarReset}>
          <header className="acceso-encabezado">
            <p className="acceso-etiqueta">Seguridad de tu cuenta</p>
            <h2>Crear nueva contraseña</h2>
            <p>Elegí una contraseña segura para volver a ingresar.</p>
          </header>
          <div className="campo"><label htmlFor="new-password">Nueva contraseña</label>
            <input id="new-password" type="password" minLength={8} maxLength={128}
              value={password} onChange={(evento) => setPassword(evento.target.value)} required />
            <small>Mínimo 8 caracteres.</small></div>
          <div className="campo"><label htmlFor="repeat-password">Repetir contraseña</label>
            <input id="repeat-password" type="password" minLength={8} maxLength={128}
              value={repetirPassword} onChange={(evento) => setRepetirPassword(evento.target.value)} required /></div>
          <button type="submit" disabled={cargando}>{cargando ? "Guardando…" : "Actualizar contraseña"}</button>
          {mensaje && <p className={`mensaje-login ${mensaje === "Tu contraseña fue actualizada." ? "mensaje-exito" : "mensaje-error"}`} role="status">{mensaje}</p>}
          <button type="button" className="boton-secundario" onClick={volverAlLogin}>Volver a iniciar sesión</button>
        </form>}

        {vistaAcceso === "login" && <form className="formulario-acceso" onSubmit={manejarInicioSesion}>
          <header className="acceso-encabezado acceso-encabezado-login">
            <p className="acceso-etiqueta">Acceso profesional</p>
            <h2>Iniciar sesión</h2>
          </header>
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
                "usuario@turnelia.com.ar"
              }
              required
            />
          </div>

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

          <button type="button" className="boton-enlace olvide-password" onClick={() => {
            navegar("/forgot-password"); setVistaAcceso("forgot"); setMensaje("");
          }}>¿Olvidaste tu contraseña?</button>

          <button
            type="submit"
            disabled={cargando}
          >
            {cargando
              ? "Ingresando..."
              : "Iniciar sesión"}
          </button>

          {mensaje && (
            <p className="mensaje-login mensaje-error" role="alert">
              {mensaje}
            </p>
          )}
        </form>}
        </section>
        <p className="acceso-pie">Gestión profesional con una experiencia humana.</p>
      </div>
    </main>
  );
}

export default App;
