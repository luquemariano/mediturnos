import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";

import "./MiDisponibilidad.css";
import Icono from "./Icono";
import ProfesionalShell from "./ProfesionalShell";
import { crearDisponibilidad, obtenerDisponibilidadesProfesional } from "../services/disponibilidadService";
import { obtenerMiPerfilProfesional } from "../services/profesionalService";
import type { Disponibilidad } from "../types/disponibilidad";
import { etiquetaPeriodo, periodoDesdeHora } from "../utils/periodoDia";

const DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

type MiDisponibilidadProps = {
  nombre: string;
  onVolver: () => void;
  onAbrirAgenda: () => void;
  onAbrirPerfil: () => void;
  onCerrarSesion: () => void;
};

function detalleError(error: unknown, alternativo: string): string {
  if (!axios.isAxiosError(error)) return alternativo;
  const detalle = error.response?.data?.detail;
  if (typeof detalle === "string") return detalle;
  if (Array.isArray(detalle)) {
    return detalle
      .map((item) => typeof item?.msg === "string" ? item.msg : null)
      .filter(Boolean).join(" ") || alternativo;
  }
  return alternativo;
}

function ordenar(items: Disponibilidad[]): Disponibilidad[] {
  return [...items].sort((a, b) =>
    a.dia_semana - b.dia_semana || a.hora_inicio.localeCompare(b.hora_inicio)
  );
}

function SkeletonDisponibilidad() {
  return <div className="mi-disp-skeleton" aria-label="Cargando disponibilidad">
    <div className="mi-disp-skeleton-semana">
      {DIAS.map((dia, indice) => <span key={dia} className={indice % 3 === 0 ? "con-franja" : undefined} />)}
    </div>
    <div className="mi-disp-skeleton-formulario"><span /><i /><i /><i /></div>
  </div>;
}

export default function MiDisponibilidad({
  nombre,
  onVolver,
  onAbrirAgenda,
  onAbrirPerfil,
  onCerrarSesion,
}: MiDisponibilidadProps) {
  const [profesionalId, setProfesionalId] = useState<number | null>(null);
  const [items, setItems] = useState<Disponibilidad[]>([]);
  const [dia, setDia] = useState("0");
  const [inicio, setInicio] = useState("");
  const [fin, setFin] = useState("");
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [formularioAbierto, setFormularioAbierto] = useState(false);
  const [errorCarga, setErrorCarga] = useState("");
  const [errorFormulario, setErrorFormulario] = useState("");
  const [exito, setExito] = useState("");
  const selectorDia = useRef<HTMLSelectElement>(null);
  const inputInicio = useRef<HTMLInputElement>(null);
  const inputFin = useRef<HTMLInputElement>(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    setErrorCarga("");
    try {
      const perfil = await obtenerMiPerfilProfesional();
      setProfesionalId(perfil.id);
      setItems(ordenar(await obtenerDisponibilidadesProfesional(perfil.id)));
    } catch (error) {
      setErrorCarga(detalleError(error, "No pudimos cargar tu disponibilidad."));
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => { void cargar(); }, [cargar]);

  const porDia = useMemo(() => DIAS.map((_, indice) =>
    items.filter((item) => item.dia_semana === indice)
  ), [items]);
  const diasConfigurados = porDia.filter((franjas) => franjas.length > 0).length;

  function abrirFormulario(indice?: number) {
    if (indice !== undefined) setDia(String(indice));
    setFormularioAbierto(true);
    setErrorFormulario("");
    setExito("");
    window.setTimeout(() => selectorDia.current?.focus(), 0);
  }

  async function registrar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (guardando || profesionalId === null) return;
    setErrorFormulario("");
    setExito("");
    if (!inicio) {
      setErrorFormulario("Ingresá la hora de inicio.");
      inputInicio.current?.focus();
      return;
    }
    if (!fin) {
      setErrorFormulario("Ingresá la hora de finalización.");
      inputFin.current?.focus();
      return;
    }
    if (fin <= inicio) {
      setErrorFormulario("La hora de finalización debe ser posterior a la de inicio.");
      inputFin.current?.focus();
      return;
    }
    setGuardando(true);
    try {
      const nueva = await crearDisponibilidad({
        profesional_id: profesionalId,
        dia_semana: Number(dia),
        hora_inicio: inicio,
        hora_fin: fin,
      });
      setItems((actuales) => ordenar([...actuales, nueva]));
      setInicio("");
      setFin("");
      setExito("Franja agregada correctamente.");
    } catch (error) {
      setErrorFormulario(detalleError(error, "No pudimos agregar la franja."));
    } finally {
      setGuardando(false);
    }
  }

  const formulario = <aside className={`mi-disp-formulario-panel${items.length === 0 ? " es-primera" : ""}`} aria-labelledby="mi-disp-formulario-titulo">
    <span>Nuevo horario habitual</span>
    <h2 id="mi-disp-formulario-titulo">{items.length === 0 ? "Configurá tu primera franja de atención." : "Agregar una franja"}</h2>
    <p>Elegí el día y el intervalo en que atendés.</p>
    <form onSubmit={registrar} noValidate>
      <label htmlFor="mi-disp-dia">Día
        <select ref={selectorDia} id="mi-disp-dia" value={dia} disabled={guardando} onChange={(evento) => setDia(evento.target.value)}>
          {DIAS.map((nombreDia, indice) => <option value={indice} key={nombreDia}>{nombreDia}</option>)}
        </select>
      </label>
      <div className="mi-disp-horas">
        <label htmlFor="mi-disp-inicio">Desde
          <input ref={inputInicio} id="mi-disp-inicio" type="time" value={inicio} disabled={guardando} required onChange={(evento) => setInicio(evento.target.value)} />
        </label>
        <label htmlFor="mi-disp-fin">Hasta
          <input ref={inputFin} id="mi-disp-fin" type="time" value={fin} disabled={guardando} required onChange={(evento) => setFin(evento.target.value)} />
        </label>
      </div>
      <button type="submit" disabled={guardando || profesionalId === null}>{guardando ? "Guardando…" : "Agregar franja"}</button>
      {errorFormulario && <p className="mi-disp-feedback error" role="alert">{errorFormulario}</p>}
      {exito && <p className="mi-disp-feedback exito" role="status">{exito}</p>}
    </form>
  </aside>;

  return <ProfesionalShell
    activo="disponibilidad"
    nombre={nombre}
    tituloTopbar="Mi disponibilidad"
    onAbrirInicio={onVolver}
    onAbrirAgenda={onAbrirAgenda}
    onAbrirDisponibilidad={() => undefined}
    onAbrirPerfil={onAbrirPerfil}
    onCerrarSesion={onCerrarSesion}
    accionTopbar={<button type="button" className="prof-enlace-topbar" onClick={onVolver}>Volver a inicio <Icono nombre="flecha" /></button>}
  >
    <div className="mi-disp-contenido">
      <header className="mi-disp-cabecera">
        <div><h1>Mi disponibilidad</h1><p>Definí los días y horarios en que atendés.</p></div>
        {!cargando && !errorCarga && <p><strong>{diasConfigurados}</strong> día{diasConfigurados === 1 ? "" : "s"} configurado{diasConfigurados === 1 ? "" : "s"}</p>}
      </header>

      {cargando ? <SkeletonDisponibilidad /> : <div className="mi-disp-layout">
        <section className="mi-disp-semana" aria-labelledby="mi-disp-semana-titulo">
          <header><div><span>Semana habitual</span><h2 id="mi-disp-semana-titulo">Tu semana</h2><p>Configurá los días y horarios en los que atendés normalmente cada semana.</p></div><button type="button" onClick={() => abrirFormulario()}>Agregar franja</button></header>
          {errorCarga ? <div className="mi-disp-error-carga" role="alert"><h3>No pudimos cargar tu disponibilidad.</h3><p>{errorCarga}</p><button type="button" onClick={() => void cargar()}><Icono nombre="recargar" />Reintentar</button></div>
          : <ol>
            {DIAS.map((nombreDia, indice) => {
              const franjas = porDia[indice];
              return <li key={nombreDia} className={franjas.length === 0 ? "sin-franjas" : undefined}>
                <h3>{nombreDia}</h3>
                <div className="mi-disp-franjas">
                  {franjas.length === 0 ? <p>Sin disponibilidad</p> : franjas.map((franja) => <div key={franja.id} className="mi-disp-franja">
                    <i aria-hidden="true" /><small>{etiquetaPeriodo(periodoDesdeHora(franja.hora_inicio))}</small>
                    <strong>{franja.hora_inicio.slice(0, 5)}–{franja.hora_fin.slice(0, 5)}</strong>
                  </div>)}
                </div>
                <button type="button" onClick={() => abrirFormulario(indice)}>{franjas.length === 0 ? "Agregar franja" : "Agregar otra franja"}</button>
              </li>;
            })}
          </ol>}
        </section>

        <button type="button" className="mi-disp-abrir-movil" aria-expanded={formularioAbierto} onClick={() => formularioAbierto ? setFormularioAbierto(false) : abrirFormulario()}>{formularioAbierto ? "Cerrar formulario" : "Agregar franja"}</button>
        <div className={`mi-disp-formulario-contenedor${formularioAbierto ? " esta-abierto" : ""}`}>{formulario}</div>
      </div>}
    </div>
  </ProfesionalShell>;
}
