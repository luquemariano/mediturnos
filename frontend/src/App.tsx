import { useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";

import "./App.css";
import {
  iniciarSesion,
  obtenerUsuarioActual,
} from "./services/authService";
import type { UsuarioActual } from "./types/auth";

function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [cargando, setCargando] = useState(false);
  const [usuario, setUsuario] = useState<UsuarioActual | null>(
    null,
  );

  async function manejarInicioSesion(
    evento: FormEvent<HTMLFormElement>,
  ) {
    evento.preventDefault();

    setMensaje("");
    setCargando(true);

    try {
      const respuesta = await iniciarSesion({
        email,
        password,
      });

      localStorage.setItem(
        "access_token",
        respuesta.access_token,
      );

      const usuarioActual = await obtenerUsuarioActual();

      setUsuario(usuarioActual);
      setMensaje("");
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detalle = error.response?.data?.detail;

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
    localStorage.removeItem("access_token");

    setUsuario(null);
    setEmail("");
    setPassword("");
    setMensaje("");
  }

  if (usuario) {
    return (
      <main className="pagina-login">
        <section className="tarjeta-login tarjeta-bienvenida">
          <div className="marca">
            <span className="marca-icono">+</span>

            <div>
              <h1>MediTurnos</h1>
              <p>Gestión médica simple y segura</p>
            </div>
          </div>

          <div className="usuario-bienvenida">
            <p className="etiqueta-bienvenida">
              Sesión iniciada
            </p>

            <h2>
              Bienvenido, {usuario.nombre}
            </h2>

            <p>
              Rol:{" "}
              <strong>{usuario.rol}</strong>
            </p>

            <p>
              {usuario.email}
            </p>
          </div>

          <button
            type="button"
            className="boton-cerrar-sesion"
            onClick={cerrarSesion}
          >
            Cerrar sesión
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="pagina-login">
      <section className="tarjeta-login">
        <div className="marca">
          <span className="marca-icono">+</span>

          <div>
            <h1>MediTurnos</h1>
            <p>Gestión médica simple y segura</p>
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
                setEmail(evento.target.value)
              }
              placeholder="usuario@mediturnos.com"
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
                setPassword(evento.target.value)
              }
              placeholder="Ingresá tu contraseña"
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