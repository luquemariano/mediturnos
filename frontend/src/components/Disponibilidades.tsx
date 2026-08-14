import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";

import "./Disponibilidades.css";
import {
  crearDisponibilidad,
  obtenerDisponibilidades,
  obtenerDisponibilidadesProfesional,
} from "../services/disponibilidadService";
import { obtenerProfesionales } from "../services/profesionalService";
import type { Disponibilidad } from "../types/disponibilidad";
import type { Profesional } from "../types/profesional";

type DisponibilidadesProps = { onVolver: () => void };

const diasSemana = [
  "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo",
];

function detalleError(error: unknown, alternativo: string): string {
  if (!axios.isAxiosError(error)) return "Ocurrió un error inesperado.";
  const detalle = error.response?.data?.detail;
  if (typeof detalle === "string") return detalle;
  if (Array.isArray(detalle)) {
    return detalle
      .map((item) => typeof item?.msg === "string" ? item.msg : null)
      .filter(Boolean)
      .join(" ") || alternativo;
  }
  return alternativo;
}

function Disponibilidades({ onVolver }: DisponibilidadesProps) {
  const [disponibilidades, setDisponibilidades] = useState<Disponibilidad[]>([]);
  const [profesionales, setProfesionales] = useState<Profesional[]>([]);
  const [filtro, setFiltro] = useState("");
  const [profesionalId, setProfesionalId] = useState("");
  const [diaSemana, setDiaSemana] = useState("0");
  const [horaInicio, setHoraInicio] = useState("");
  const [horaFin, setHoraFin] = useState("");
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [errorListado, setErrorListado] = useState("");
  const [errorFormulario, setErrorFormulario] = useState("");
  const [exito, setExito] = useState("");

  const cargarDatos = useCallback(async () => {
    setCargando(true);
    setErrorListado("");
    try {
      const [horarios, profesionalesDisponibles] = await Promise.all([
        obtenerDisponibilidades(), obtenerProfesionales(),
      ]);
      setDisponibilidades(horarios);
      setProfesionales(profesionalesDisponibles);
      setFiltro("");
    } catch (error) {
      setErrorListado(detalleError(error, "No se pudieron cargar las disponibilidades."));
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => { void cargarDatos(); }, [cargarDatos]);

  const profesionalesPorId = useMemo(() => new Map(
    profesionales.map((profesional) => [
      profesional.id, `${profesional.nombre} ${profesional.apellido}`,
    ]),
  ), [profesionales]);

  async function consultarProfesional(valor: string) {
    setFiltro(valor);
    setErrorListado("");
    setExito("");
    setCargando(true);
    try {
      setDisponibilidades(valor
        ? await obtenerDisponibilidadesProfesional(Number(valor))
        : await obtenerDisponibilidades());
    } catch (error) {
      setErrorListado(detalleError(error, "No se pudieron consultar las disponibilidades."));
    } finally {
      setCargando(false);
    }
  }

  async function registrar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setErrorFormulario("");
    setExito("");
    setGuardando(true);
    try {
      const nueva = await crearDisponibilidad({
        profesional_id: Number(profesionalId),
        dia_semana: Number(diaSemana),
        hora_inicio: horaInicio,
        hora_fin: horaFin,
      });
      if (!filtro || Number(filtro) === nueva.profesional_id) {
        setDisponibilidades((actuales) => [...actuales, nueva]);
      }
      setDiaSemana("0");
      setHoraInicio("");
      setHoraFin("");
      setExito("La disponibilidad fue registrada correctamente.");
    } catch (error) {
      setErrorFormulario(detalleError(error, "No se pudo registrar la disponibilidad."));
    } finally {
      setGuardando(false);
    }
  }

  return (
    <main className="pagina-dashboard">
      <section className="dashboard">
        <header className="dashboard-encabezado">
          <div className="marca dashboard-marca">
            <span className="marca-icono">+</span>
            <div><h1>Turnelia</h1><p>Gestión de disponibilidades</p></div>
          </div>
          <button type="button" className="boton-cerrar-sesion" onClick={onVolver}>
            Volver al panel
          </button>
        </header>

        <section className="disponibilidades-contenido">
          <div className="disponibilidades-cabecera">
            <p className="disponibilidades-etiqueta">Módulo</p>
            <h2>Disponibilidades</h2>
            <p>Configurá los días y horarios de atención profesional.</p>
          </div>

          <form className="disponibilidades-formulario" onSubmit={registrar}>
            <h3>Nueva disponibilidad</h3>
            <div className="disponibilidades-campos">
              <label>Profesional
                <select value={profesionalId} onChange={(e) => setProfesionalId(e.target.value)} required>
                  <option value="">Seleccionar profesional</option>
                  {profesionales.map((p) => <option key={p.id} value={p.id}>{p.nombre} {p.apellido}</option>)}
                </select>
              </label>
              <label>Día de la semana
                <select value={diaSemana} onChange={(e) => setDiaSemana(e.target.value)}>
                  {diasSemana.map((dia, indice) => <option key={dia} value={indice}>{dia}</option>)}
                </select>
              </label>
              <label>Hora de inicio
                <input type="time" value={horaInicio} onChange={(e) => setHoraInicio(e.target.value)} required />
              </label>
              <label>Hora de fin
                <input type="time" value={horaFin} onChange={(e) => setHoraFin(e.target.value)} required />
              </label>
              <button type="submit" disabled={guardando}>
                {guardando ? "Guardando..." : "Registrar disponibilidad"}
              </button>
            </div>
            {errorFormulario && <p className="disponibilidades-error" role="alert">{errorFormulario}</p>}
          </form>

          <div className="disponibilidades-herramientas">
            <label htmlFor="filtro-profesional">Consultar por profesional</label>
            <select id="filtro-profesional" value={filtro} onChange={(e) => void consultarProfesional(e.target.value)}>
              <option value="">Todos los profesionales</option>
              {profesionales.map((p) => <option key={p.id} value={p.id}>{p.nombre} {p.apellido}</option>)}
            </select>
          </div>

          {exito && <p className="disponibilidades-exito" role="status">{exito}</p>}
          {cargando && <div className="disponibilidades-estado"><span className="disponibilidades-carga" /><p>Cargando disponibilidades...</p></div>}
          {!cargando && errorListado && <div className="disponibilidades-estado disponibilidades-error"><p>{errorListado}</p><button type="button" className="boton-cerrar-sesion" onClick={() => void cargarDatos()}>Reintentar</button></div>}
          {!cargando && !errorListado && disponibilidades.length === 0 && <div className="disponibilidades-estado"><h3>No hay disponibilidades registradas</h3><p>Podés crear la primera desde el formulario.</p></div>}
          {!cargando && !errorListado && disponibilidades.length > 0 && (
            <div className="tabla-disponibilidades-contenedor">
              <table className="tabla-disponibilidades">
                <thead><tr><th>Día</th><th>Hora de inicio</th><th>Hora de fin</th><th>Profesional</th><th>Estado</th></tr></thead>
                <tbody>{disponibilidades.map((item) => (
                  <tr key={item.id}>
                    <td>{diasSemana[item.dia_semana]}</td>
                    <td>{item.hora_inicio.slice(0, 5)}</td>
                    <td>{item.hora_fin.slice(0, 5)}</td>
                    <td>{profesionalesPorId.get(item.profesional_id) ?? `Profesional #${item.profesional_id}`}</td>
                    <td><span className={item.activa ? "disponibilidad-activa" : "disponibilidad-inactiva"}>{item.activa ? "Activa" : "Inactiva"}</span></td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
        </section>
      </section>
    </main>
  );
}

export default Disponibilidades;
