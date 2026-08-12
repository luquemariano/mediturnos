import { useEffect, useState } from "react";

import { obtenerMiPerfilPaciente } from "../services/pacienteService";
import { obtenerMiPerfilProfesional } from "../services/profesionalService";

type Perfil = { nombre: string; apellido: string; email: string | null; telefono: string | null };

export default function PerfilPropio({ tipo, onVolver }: {
  tipo: "profesional" | "paciente";
  onVolver: () => void;
}) {
  const [perfil, setPerfil] = useState<Perfil | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const cargar = tipo === "profesional"
      ? obtenerMiPerfilProfesional
      : obtenerMiPerfilPaciente;
    void cargar().then(setPerfil).catch(() => setError("No se pudo cargar el perfil."));
  }, [tipo]);

  return <main className="pagina-dashboard"><section className="dashboard">
    <header className="dashboard-encabezado"><h1>Mi perfil</h1>
      <button type="button" className="boton-cerrar-sesion" onClick={onVolver}>Volver al panel</button>
    </header>
    {error && <p role="alert">{error}</p>}
    {!perfil && !error && <p>Cargando perfil...</p>}
    {perfil && <dl><dt>Nombre</dt><dd>{perfil.nombre} {perfil.apellido}</dd><dt>Email</dt><dd>{perfil.email ?? "Sin email"}</dd><dt>Teléfono</dt><dd>{perfil.telefono ?? "Sin teléfono"}</dd></dl>}
  </section></main>;
}
