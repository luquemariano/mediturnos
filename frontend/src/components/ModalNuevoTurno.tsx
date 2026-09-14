import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";

import { obtenerPacientes } from "../services/pacienteService";
import { obtenerPrestaciones } from "../services/prestacionService";
import { obtenerProfesionales } from "../services/profesionalService";
import {
  crearTurno,
  obtenerHorariosLibres,
} from "../services/turnoService";
import type { Paciente } from "../types/paciente";
import type { Prestacion } from "../types/prestacion";
import type { Profesional } from "../types/profesional";
import type { HorarioLibre, Turno } from "../types/turno";
import {
  fechaActualNegocio,
  formatearHoraTurno,
} from "../utils/fechaTurno";

type ModalNuevoTurnoProps = {
  onCerrar: () => void;
  onTurnoCreado: (turno: Turno) => void;
};

function mensajeError(error: unknown, alternativo: string): string {
  if (!axios.isAxiosError(error)) return "Ocurrió un error inesperado.";

  const estado = error.response?.status;
  const detalle = error.response?.data?.detail;
  if (typeof detalle === "string") return detalle;
  if (estado === 401) return "La sesión venció o no es válida. Iniciá sesión nuevamente.";
  if (estado === 403) return "No tenés permisos para realizar esta operación.";
  if (estado === 409) return "El horario ya no está disponible. Elegí otro horario.";
  if (estado === 422 && Array.isArray(detalle)) {
    const mensajes = detalle
      .map((item) => typeof item?.msg === "string" ? item.msg : null)
      .filter(Boolean)
      .join(" ");
    return mensajes || "Revisá los datos ingresados.";
  }
  return alternativo;
}

function formatearHorario(fechaHora: string): string {
  return `${formatearHoraTurno(fechaHora)} hs`;
}

function ModalNuevoTurno({ onCerrar, onTurnoCreado }: ModalNuevoTurnoProps) {
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [profesionales, setProfesionales] = useState<Profesional[]>([]);
  const [prestaciones, setPrestaciones] = useState<Prestacion[]>([]);
  const [horarios, setHorarios] = useState<HorarioLibre[]>([]);
  const [pacienteId, setPacienteId] = useState("");
  const [profesionalId, setProfesionalId] = useState("");
  const [prestacionId, setPrestacionId] = useState("");
  const [fecha, setFecha] = useState("");
  const [fechaHora, setFechaHora] = useState("");
  const [observaciones, setObservaciones] = useState("");
  const [cargandoDatos, setCargandoDatos] = useState(true);
  const [consultando, setConsultando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function cargarOpciones() {
      try {
        const [pacientesDatos, profesionalesDatos, prestacionesDatos] =
          await Promise.all([
            obtenerPacientes(), obtenerProfesionales(), obtenerPrestaciones(),
          ]);
        setPacientes(pacientesDatos.filter((item) => item.activo));
        setProfesionales(profesionalesDatos.filter((item) => item.activo));
        setPrestaciones(prestacionesDatos.filter((item) => item.activa));
      } catch (err) {
        setError(mensajeError(err, "No se pudieron cargar las opciones del turno."));
      } finally {
        setCargandoDatos(false);
      }
    }
    void cargarOpciones();
  }, []);

  const prestacionesFiltradas = useMemo(
    () => prestaciones.filter(
      (item) => item.profesional_id === Number(profesionalId),
    ),
    [prestaciones, profesionalId],
  );

  function seleccionarProfesional(valor: string) {
    setProfesionalId(valor);
    setPrestacionId("");
    setFecha("");
    setFechaHora("");
    setHorarios([]);
    setError("");
  }

  function seleccionarPrestacion(valor: string) {
    setPrestacionId(valor);
    setFecha("");
    setFechaHora("");
    setHorarios([]);
    setError("");
  }

  async function consultarHorarios(nuevaFecha: string) {
    setFecha(nuevaFecha);
    setFechaHora("");
    setHorarios([]);
    setError("");
    if (!nuevaFecha || !prestacionId) return;

    setConsultando(true);
    try {
      setHorarios(await obtenerHorariosLibres(Number(prestacionId), nuevaFecha));
    } catch (err) {
      setError(mensajeError(err, "No se pudieron consultar los horarios libres."));
    } finally {
      setConsultando(false);
    }
  }

  async function guardar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setError("");
    setGuardando(true);
    try {
      const turno = await crearTurno({
        paciente_id: Number(pacienteId),
        prestacion_id: Number(prestacionId),
        fecha_hora: fechaHora,
        observaciones: observaciones.trim() || null,
      });
      onTurnoCreado(turno);
    } catch (err) {
      setError(mensajeError(err, "No se pudo crear el turno."));
      if (axios.isAxiosError(err) && err.response?.status === 409 && fecha) {
        try {
          setHorarios(await obtenerHorariosLibres(Number(prestacionId), fecha));
          setFechaHora("");
        } catch {
          setHorarios([]);
        }
      }
    } finally {
      setGuardando(false);
    }
  }

  const fechaMinima = fechaActualNegocio();

  return (
    <div className="modal-turno-fondo" role="presentation">
      <section className="modal-turno" role="dialog" aria-modal="true" aria-labelledby="titulo-nuevo-turno">
        <header className="modal-turno-encabezado">
          <div><p className="turnos-etiqueta">Agenda</p><h2 id="titulo-nuevo-turno">Nuevo turno</h2></div>
          <button type="button" onClick={onCerrar} aria-label="Cerrar">×</button>
        </header>

        <form className="formulario-turno" onSubmit={guardar}>
          {cargandoDatos ? <p className="formulario-turno-estado">Cargando opciones...</p> : (
            <div className="formulario-turno-campos">
              <label>Paciente
                <select value={pacienteId} onChange={(e) => setPacienteId(e.target.value)} required>
                  <option value="">Seleccionar paciente</option>
                  {pacientes.map((p) => <option key={p.id} value={p.id}>{p.nombre} {p.apellido} · DNI {p.dni}</option>)}
                </select>
              </label>
              <label>Profesional
                <select value={profesionalId} onChange={(e) => seleccionarProfesional(e.target.value)} required>
                  <option value="">Seleccionar profesional</option>
                  {profesionales.map((p) => <option key={p.id} value={p.id}>{p.nombre} {p.apellido}</option>)}
                </select>
              </label>
              <label>Prestación
                <select value={prestacionId} onChange={(e) => seleccionarPrestacion(e.target.value)} disabled={!profesionalId} required>
                  <option value="">{profesionalId ? "Seleccionar prestación" : "Primero seleccioná un profesional"}</option>
                  {prestacionesFiltradas.map((p) => <option key={p.id} value={p.id}>{p.nombre} · {p.duracion_minutos} min</option>)}
                </select>
              </label>
              <label>Fecha
                <input type="date" min={fechaMinima} value={fecha} onChange={(e) => void consultarHorarios(e.target.value)} disabled={!prestacionId} required />
              </label>
              <fieldset className="horarios-turno" disabled={!fecha || consultando}>
                <legend>Horario disponible</legend>
                {consultando && <p>Consultando horarios...</p>}
                {!consultando && fecha && horarios.length === 0 && <p>No hay horarios disponibles para esta fecha.</p>}
                {!consultando && horarios.map((horario) => (
                  <label key={horario.fecha_hora} className={fechaHora === horario.fecha_hora ? "seleccionado" : ""}>
                    <input type="radio" name="fecha-hora" value={horario.fecha_hora} checked={fechaHora === horario.fecha_hora} onChange={(e) => setFechaHora(e.target.value)} required />
                    {formatearHorario(horario.fecha_hora)}
                  </label>
                ))}
              </fieldset>
              <label className="campo-observaciones">Observaciones
                <textarea value={observaciones} onChange={(e) => setObservaciones(e.target.value)} maxLength={1000} rows={3} placeholder="Información opcional para el turno" />
              </label>
            </div>
          )}

          {error && <p className="mensaje-turnos-error" role="alert">{error}</p>}
          <footer className="formulario-turno-acciones">
            <button type="button" className="boton-cerrar-sesion" onClick={onCerrar}>Cancelar</button>
            <button type="submit" className="boton-primario" disabled={cargandoDatos || guardando || !fechaHora}>
              {guardando ? "Creando..." : "Crear turno"}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

export default ModalNuevoTurno;
