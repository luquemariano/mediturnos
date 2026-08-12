import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { crearDisponibilidad, obtenerDisponibilidadesProfesional } from "../services/disponibilidadService";
import { obtenerMiPerfilProfesional } from "../services/profesionalService";
import type { Disponibilidad } from "../types/disponibilidad";

const dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

export default function MiDisponibilidad({ onVolver }: { onVolver: () => void }) {
  const [profesionalId, setProfesionalId] = useState<number | null>(null);
  const [items, setItems] = useState<Disponibilidad[]>([]);
  const [dia, setDia] = useState("0");
  const [inicio, setInicio] = useState("");
  const [fin, setFin] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { void obtenerMiPerfilProfesional().then(async (perfil) => { setProfesionalId(perfil.id); setItems(await obtenerDisponibilidadesProfesional(perfil.id)); }).catch(() => setError("No se pudo cargar tu disponibilidad.")); }, []);
  async function registrar(evento: FormEvent) { evento.preventDefault(); if (profesionalId === null) return; setError(""); try { const nueva = await crearDisponibilidad({ profesional_id: profesionalId, dia_semana: Number(dia), hora_inicio: inicio, hora_fin: fin }); setItems((actuales) => [...actuales, nueva]); setInicio(""); setFin(""); } catch { setError("No se pudo registrar la disponibilidad."); } }
  return <main className="pagina-dashboard"><section className="dashboard"><header className="dashboard-encabezado"><h1>Mi disponibilidad</h1><button type="button" className="boton-cerrar-sesion" onClick={onVolver}>Volver al panel</button></header><form className="disponibilidades-formulario" onSubmit={registrar}><select aria-label="Día de la semana" value={dia} onChange={(e) => setDia(e.target.value)}>{dias.map((nombre, indice) => <option value={indice} key={nombre}>{nombre}</option>)}</select><input aria-label="Hora de inicio" type="time" value={inicio} onChange={(e) => setInicio(e.target.value)} required /><input aria-label="Hora de fin" type="time" value={fin} onChange={(e) => setFin(e.target.value)} required /><button type="submit" disabled={profesionalId === null}>Registrar disponibilidad</button></form>{error && <p role="alert">{error}</p>}<ul>{items.map((item) => <li key={item.id}>{dias[item.dia_semana]} {item.hora_inicio.slice(0, 5)}–{item.hora_fin.slice(0, 5)}</li>)}</ul></section></main>;
}
