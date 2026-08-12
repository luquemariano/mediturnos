import { useState } from "react";
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
import {
  iniciarSesion,
  obtenerUsuarioActual,
} from "./services/authService";
import type { UsuarioActual } from "./types/auth";


type Vista =
  | "dashboard"
  | "pacientes"
  | "especialidades"
  | "prestaciones"
  | "profesionales"
  | "turnos"
  | "disponibilidades";


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

  const [vista, setVista] =
    useState<Vista>("dashboard");


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

      const usuarioActual =
        await obtenerUsuarioActual();

      setUsuario(usuarioActual);
      setVista("dashboard");
    } catch (error) {
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
      return (
        <Turnos
          onVolver={() =>
            setVista("dashboard")
          }
        />
      );
    }

    if (
      vista === "disponibilidades"
      && ["administrador", "recepcionista"].includes(usuario.rol)
    ) {
      return (
        <Disponibilidades
          onVolver={() => setVista("dashboard")}
        />
      );
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
