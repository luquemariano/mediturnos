import { useEffect, useState } from "react";
import axios from "axios";

import type { Turno } from "../types/turno";
import {
  cancelarMiTurno,
  finalizarMiTurno,
  marcarAusenteMiTurno,
  obtenerMiAgendaProfesional,
  obtenerMisTurnosPaciente,
} from "../services/turnoService";

type AgendaPropiaProps = {
  tipo: "profesional" | "paciente";
  onVolver: () => void;
};

function detalleError(error: unknown): string {
  if (axios.isAxiosError(error) && typeof error.response?.data?.detail === "string") {
    return error.response.data.detail;
  }
  return "No se pudo cargar la información.";
}

export default function AgendaPropia({ tipo, onVolver }: AgendaPropiaProps) {
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const cargar = tipo === "profesional"
      ? obtenerMiAgendaProfesional
      : obtenerMisTurnosPaciente;
    void cargar()
      .then(setTurnos)
      .catch((motivo) => setError(detalleError(motivo)))
      .finally(() => setCargando(false));
  }, [tipo]);

  async function actualizar(turno: Turno, accion: "cancelar" | "finalizar" | "ausente") {
    setError("");
    try {
      const actualizado = accion === "cancelar"
        ? await cancelarMiTurno(turno.id)
        : accion === "finalizar"
          ? await finalizarMiTurno(turno.id)
          : await marcarAusenteMiTurno(turno.id);
      setTurnos((actuales) => actuales.map((item) =>
        item.id === actualizado.id ? actualizado : item
      ));
    } catch (motivo) {
      setError(detalleError(motivo));
    }
  }

  return (
    <main className="pagina-dashboard">
      <section className="dashboard">
        <header className="dashboard-encabezado">
          <h1>{tipo === "profesional" ? "Mi agenda" : "Mis turnos"}</h1>
          <button type="button" className="boton-cerrar-sesion" onClick={onVolver}>Volver al panel</button>
        </header>
        {cargando && <p>Cargando turnos...</p>}
        {error && <p role="alert">{error}</p>}
        {!cargando && !error && turnos.length === 0 && <p>No hay turnos registrados.</p>}
        <div className="agenda-lista">
          {turnos.map((turno) => (
            <article className="turno-tarjeta" key={turno.id}>
              <div className="turno-informacion">
                <h2>{turno.prestacion_nombre}</h2>
                <p>{turno.paciente_nombre} · {turno.fecha_hora}</p>
                <strong>{turno.estado}</strong>
              </div>
              <div className="turno-acciones">
                {tipo === "paciente" && ["reservado", "confirmado"].includes(turno.estado) && (
                  <button type="button" onClick={() => void actualizar(turno, "cancelar")}>Cancelar turno</button>
                )}
                {tipo === "profesional" && ["reservado", "confirmado"].includes(turno.estado) && (<>
                  <button type="button" onClick={() => void actualizar(turno, "finalizar")}>Finalizar</button>
                  <button type="button" onClick={() => void actualizar(turno, "ausente")}>Marcar ausente</button>
                </>)}
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
