import { useState } from "react";
import "./App.css";

function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function iniciarSesion(evento: React.FormEvent<HTMLFormElement>) {
    evento.preventDefault();

    console.log("Email:", email);
    console.log("Contraseña:", password);
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

        <form onSubmit={iniciarSesion}>
          <div className="campo">
            <label htmlFor="email">Correo electrónico</label>

            <input
              id="email"
              type="email"
              value={email}
              onChange={(evento) => setEmail(evento.target.value)}
              placeholder="usuario@mediturnos.com"
              required
            />
          </div>

          <div className="campo">
            <label htmlFor="password">Contraseña</label>

            <input
              id="password"
              type="password"
              value={password}
              onChange={(evento) => setPassword(evento.target.value)}
              placeholder="Ingresá tu contraseña"
              required
            />
          </div>

          <button type="submit">
            Iniciar sesión
          </button>
        </form>
      </section>
    </main>
  );
}

export default App;