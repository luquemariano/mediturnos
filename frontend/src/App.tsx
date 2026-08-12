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
import {
  iniciarSesion,
  obtenerUsuarioActual,
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


function App() {
  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [mensaje, setMensaje] =
    useState("");

  const [cargando, setCargando] =
    useState(false);

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
    if (vista === "pacientes") {
      return (
        <Pacientes
          onVolver={() =>
            setVista("dashboard")
          }
        />
      );
    }

    if (vista === "turnos") {
      if (usuario.rol === "profesional" || usuario.rol === "paciente") {
        return <AgendaPropia tipo={usuario.rol} onVolver={() => setVista("dashboard")} />;
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
        return <MiDisponibilidad onVolver={() => setVista("dashboard")} />;
      }
      if (["administrador", "recepcionista"].includes(usuario.rol)) return (
        <Disponibilidades
          onVolver={() => setVista("dashboard")}
        />
      );
    }

    if (vista === "perfil" && ["profesional", "paciente"].includes(usuario.rol)) {
      return <PerfilPropio tipo={usuario.rol as "profesional" | "paciente"} onVolver={() => setVista("dashboard")} />;
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

        <form onSubmit={manejarInicioSesion}>
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
        </form>
      </section>
    </main>
  );
}

export default App;
