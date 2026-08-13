import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";

import "./NuevoTurnoProfesional.css";
import { obtenerPacientesParaProfesional } from "../services/pacienteService";
import { obtenerPrestaciones } from "../services/prestacionService";
import { obtenerMiPerfilProfesional } from "../services/profesionalService";
import { crearMiTurnoProfesional, obtenerHorariosLibres } from "../services/turnoService";
import type { PacienteSeleccion } from "../types/paciente";
import type { Prestacion } from "../types/prestacion";
import type { HorarioLibre, Turno } from "../types/turno";
import { fechaActualNegocio, formatearHoraTurno } from "../utils/fechaTurno";

type Props = {
  onCerrar: () => void;
  onCreado: (turno: Turno) => void;
};

function detalleError(error: unknown, alternativo: string): string {
  if (!axios.isAxiosError(error)) return alternativo;
  const detalle = error.response?.data?.detail;
  if (typeof detalle === "string") return detalle;
  return error.response?.status === 409
    ? "El horario ya no está disponible. Elegí otro horario."
    : alternativo;
}

export default function NuevoTurnoProfesional({ onCerrar, onCreado }: Props) {
  const [pacientes, setPacientes] = useState<PacienteSeleccion[]>([]);
  const [prestaciones, setPrestaciones] = useState<Prestacion[]>([]);
  const [horarios, setHorarios] = useState<HorarioLibre[]>([]);
  const [pacienteId, setPacienteId] = useState("");
  const [prestacionId, setPrestacionId] = useState("");
  const [fecha, setFecha] = useState("");
  const [fechaHora, setFechaHora] = useState("");
  const [observaciones, setObservaciones] = useState("");
  const [cargando, setCargando] = useState(true);
  const [consultando, setConsultando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function cargar() {
      try {
        const [pacientesDatos, perfil, prestacionesDatos] = await Promise.all([
          obtenerPacientesParaProfesional(),
          obtenerMiPerfilProfesional(),
          obtenerPrestaciones(),
        ]);
        setPacientes(pacientesDatos);
        setPrestaciones(prestacionesDatos.filter((item) => item.activa && item.profesional_id === perfil.id));
      } catch (motivo) {
        setError(detalleError(motivo, "No pudimos cargar los datos para crear el turno."));
      } finally {
        setCargando(false);
      }
    }
    void cargar();
  }, []);

  const prestacionSeleccionada = useMemo(
    () => prestaciones.find((item) => item.id === Number(prestacionId)),
    [prestaciones, prestacionId],
  );

  async function consultar(nuevaFecha: string) {
    setFecha(nuevaFecha);
    setFechaHora("");
    setHorarios([]);
    setError("");
    if (!nuevaFecha || !prestacionId) return;
    setConsultando(true);
    try {
      setHorarios(await obtenerHorariosLibres(Number(prestacionId), nuevaFecha));
    } catch (motivo) {
      setError(detalleError(motivo, "No pudimos consultar los horarios disponibles."));
    } finally {
      setConsultando(false);
    }
  }

  async function guardar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (guardando || !fechaHora) return;
    setGuardando(true);
    setError("");
    try {
      onCreado(await crearMiTurnoProfesional({
        paciente_id: Number(pacienteId),
        prestacion_id: Number(prestacionId),
        fecha_hora: fechaHora,
        observaciones: observaciones.trim() || null,
      }));
    } catch (motivo) {
      setError(detalleError(motivo, "No pudimos crear el turno."));
      if (axios.isAxiosError(motivo) && motivo.response?.status === 409 && fecha) {
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

  return <div className="nuevo-turno-prof-fondo" role="presentation">
    <section className="nuevo-turno-prof" role="dialog" aria-modal="true" aria-labelledby="nuevo-turno-prof-titulo">
      <header><div><span>MI AGENDA</span><h2 id="nuevo-turno-prof-titulo">Nuevo turno</h2></div><button type="button" onClick={onCerrar} aria-label="Cerrar">×</button></header>
      {cargando ? <p className="nuevo-turno-prof-carga">Cargando opciones…</p> : <form onSubmit={guardar}>
        <label>Paciente<select required value={pacienteId} disabled={guardando} onChange={(evento) => setPacienteId(evento.target.value)}><option value="">Seleccionar paciente</option>{pacientes.map((paciente) => <option key={paciente.id} value={paciente.id}>{paciente.apellido}, {paciente.nombre}</option>)}</select></label>
        <label>Prestación<select required value={prestacionId} disabled={guardando} onChange={(evento) => { setPrestacionId(evento.target.value); setFecha(""); setFechaHora(""); setHorarios([]); }}><option value="">Seleccionar prestación</option>{prestaciones.map((prestacion) => <option key={prestacion.id} value={prestacion.id}>{prestacion.nombre} · {prestacion.duracion_minutos} min</option>)}</select></label>
        <label>Fecha<input type="date" min={fechaActualNegocio()} required value={fecha} disabled={guardando || !prestacionId} onChange={(evento) => void consultar(evento.target.value)} /></label>
        <fieldset disabled={guardando || !fecha || consultando}><legend>Horario disponible</legend>{consultando && <p>Consultando horarios…</p>}{!consultando && fecha && horarios.length === 0 && <p>No hay horarios disponibles para esta fecha.</p>}<div className="nuevo-turno-prof-horarios">{horarios.map((horario) => <label key={horario.fecha_hora} className={fechaHora === horario.fecha_hora ? "seleccionado" : undefined}><input type="radio" name="horario" required value={horario.fecha_hora} checked={fechaHora === horario.fecha_hora} onChange={(evento) => setFechaHora(evento.target.value)} />{formatearHoraTurno(horario.fecha_hora)}</label>)}</div></fieldset>
        <label>Observaciones <small>Opcional</small><textarea rows={3} maxLength={1000} value={observaciones} disabled={guardando} onChange={(evento) => setObservaciones(evento.target.value)} placeholder="Información útil para la atención" /></label>
        {prestacionSeleccionada && <p className="nuevo-turno-prof-resumen">Duración: {prestacionSeleccionada.duracion_minutos} minutos</p>}
        {error && <p className="nuevo-turno-prof-error" role="alert">{error}</p>}
        <footer><button type="button" onClick={onCerrar} disabled={guardando}>Cancelar</button><button type="submit" disabled={guardando || !pacienteId || !fechaHora}>{guardando ? "Guardando…" : "Confirmar turno"}</button></footer>
      </form>}
    </section>
  </div>;
}
