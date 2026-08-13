import { useCallback, useEffect, useState } from "react";

import "./PerfilPropio.css";
import ProfesionalShell from "./ProfesionalShell";
import { obtenerEspecialidades } from "../services/especialidadService";
import { obtenerMiPerfilPaciente } from "../services/pacienteService";
import { obtenerMiPerfilProfesional } from "../services/profesionalService";
import type { Especialidad } from "../types/especialidad";
import type { Paciente } from "../types/paciente";
import type { Profesional } from "../types/profesional";

type PerfilPacienteProps = {
  tipo: "paciente";
  onVolver: () => void;
};

type PerfilProfesionalProps = {
  tipo: "profesional";
  nombre: string;
  onVolver: () => void;
  onAbrirAgenda: () => void;
  onAbrirDisponibilidad: () => void;
  onAbrirPerfil: () => void;
  onCerrarSesion: () => void;
};

type PerfilPropioProps = PerfilPacienteProps | PerfilProfesionalProps;

function PerfilPaciente({ onVolver }: PerfilPacienteProps) {
  const [perfil, setPerfil] = useState<Paciente | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    void obtenerMiPerfilPaciente()
      .then(setPerfil)
      .catch(() => setError("No se pudo cargar el perfil."));
  }, []);

  return <main className="pagina-dashboard"><section className="dashboard">
    <header className="dashboard-encabezado"><h1>Mi perfil</h1>
      <button type="button" className="boton-cerrar-sesion" onClick={onVolver}>Volver al panel</button>
    </header>
    {error && <p role="alert">{error}</p>}
    {!perfil && !error && <p>Cargando perfil...</p>}
    {perfil && <dl><dt>Nombre</dt><dd>{perfil.nombre} {perfil.apellido}</dd><dt>Email</dt><dd>{perfil.email ?? "Sin email"}</dd><dt>Teléfono</dt><dd>{perfil.telefono ?? "Sin teléfono"}</dd></dl>}
  </section></main>;
}

function SkeletonPerfilProfesional() {
  return <section className="perfil-profesional-superficie perfil-profesional-skeleton" aria-label="Cargando perfil" aria-busy="true">
    <div className="perfil-skeleton-identidad">
      <span className="perfil-skeleton-linea perfil-skeleton-nombre" />
      <span className="perfil-skeleton-linea perfil-skeleton-rol" />
      <span className="perfil-skeleton-linea perfil-skeleton-matricula" />
    </div>
    <div className="perfil-skeleton-contacto">
      <span className="perfil-skeleton-linea" />
      <span className="perfil-skeleton-linea" />
    </div>
    <div className="perfil-skeleton-actividad">
      <span className="perfil-skeleton-linea" />
      <span className="perfil-skeleton-linea perfil-skeleton-especialidad" />
      <span className="perfil-skeleton-linea perfil-skeleton-especialidad" />
    </div>
  </section>;
}

function PerfilProfesional(props: PerfilProfesionalProps) {
  const [perfil, setPerfil] = useState<Profesional | null>(null);
  const [especialidades, setEspecialidades] = useState<Especialidad[]>([]);
  const [cargandoPerfil, setCargandoPerfil] = useState(true);
  const [cargandoEspecialidades, setCargandoEspecialidades] = useState(true);
  const [errorPerfil, setErrorPerfil] = useState("");
  const [errorEspecialidades, setErrorEspecialidades] = useState("");

  const cargarEspecialidades = useCallback(async () => {
    setCargandoEspecialidades(true);
    setErrorEspecialidades("");
    try {
      setEspecialidades(await obtenerEspecialidades());
    } catch {
      setErrorEspecialidades("No pudimos cargar el detalle de tus especialidades.");
    } finally {
      setCargandoEspecialidades(false);
    }
  }, []);

  const cargarPerfil = useCallback(async () => {
    setCargandoPerfil(true);
    setErrorPerfil("");
    try {
      setPerfil(await obtenerMiPerfilProfesional());
    } catch {
      setPerfil(null);
      setErrorPerfil("No pudimos cargar tu perfil.");
    } finally {
      setCargandoPerfil(false);
    }
  }, []);

  useEffect(() => {
    void cargarPerfil();
    void cargarEspecialidades();
  }, [cargarEspecialidades, cargarPerfil]);

  const nombreShell = perfil ? `${perfil.nombre} ${perfil.apellido}` : props.nombre;
  const especialidadesPorId = new Map(especialidades.map((item) => [item.id, item.nombre]));

  return <ProfesionalShell
    activo="perfil"
    nombre={nombreShell}
    tituloTopbar="Mi perfil"
    onAbrirInicio={props.onVolver}
    onAbrirAgenda={props.onAbrirAgenda}
    onAbrirDisponibilidad={props.onAbrirDisponibilidad}
    onAbrirPerfil={props.onAbrirPerfil}
    onCerrarSesion={props.onCerrarSesion}
  >
    <div className="perfil-profesional-pagina">
      <header className="perfil-profesional-encabezado">
        <p className="perfil-profesional-eyebrow">Perfil profesional</p>
        <h1>Mi perfil</h1>
        <p>Revisá la información vinculada a tu cuenta profesional.</p>
      </header>

      {cargandoPerfil && <SkeletonPerfilProfesional />}

      {!cargandoPerfil && errorPerfil && <section className="perfil-profesional-error" role="alert">
        <h2>No pudimos cargar tu perfil.</h2>
        <p>Revisá tu conexión e intentá nuevamente.</p>
        <button type="button" onClick={() => void cargarPerfil()}>Reintentar</button>
      </section>}

      {perfil && <section className="perfil-profesional-superficie" aria-label="Información profesional">
        <div className="perfil-profesional-identidad">
          <div>
            <h2>{perfil.nombre} {perfil.apellido}</h2>
            <p className="perfil-profesional-rol">Profesional</p>
            <p className="perfil-profesional-matricula"><span>Matrícula</span> · {perfil.matricula}</p>
          </div>
          <p className={`perfil-profesional-estado ${perfil.activo ? "activo" : "inactivo"}`}>
            <span aria-hidden="true" />{perfil.activo ? "Perfil activo" : "Perfil inactivo"}
          </p>
        </div>

        <section className="perfil-profesional-contacto" aria-labelledby="perfil-contacto-titulo">
          <h3 id="perfil-contacto-titulo">Datos de contacto</h3>
          <dl>
            <div><dt>Email</dt><dd>{perfil.email ?? "No informado"}</dd></div>
            <div><dt>Teléfono</dt><dd>{perfil.telefono ?? "No informado"}</dd></div>
          </dl>
        </section>

        <section className="perfil-profesional-actividad" aria-labelledby="perfil-actividad-titulo">
          <h3 id="perfil-actividad-titulo">Actividad profesional</h3>
          {cargandoEspecialidades && <div className="perfil-actividad-cargando" aria-label="Cargando especialidades" aria-busy="true">
            <span className="perfil-skeleton-linea perfil-skeleton-especialidad" />
            <span className="perfil-skeleton-linea perfil-skeleton-especialidad" />
          </div>}
          {!cargandoEspecialidades && errorEspecialidades && <div className="perfil-actividad-error" role="status">
            <p>{errorEspecialidades}</p>
            <button type="button" onClick={() => void cargarEspecialidades()}>Reintentar</button>
          </div>}
          {!cargandoEspecialidades && !errorEspecialidades && perfil.especialidades.length === 0 &&
            <p className="perfil-actividad-vacia">Todavía no hay especialidades asociadas a este perfil.</p>}
          {!cargandoEspecialidades && !errorEspecialidades && perfil.especialidades.length > 0 && <ul>
            {perfil.especialidades.map((asignacion) => <li key={asignacion.especialidad_id}>
              <strong>{especialidadesPorId.get(asignacion.especialidad_id) ?? "Especialidad no disponible"}</strong>
              {asignacion.duracion_turno_minutos !== null &&
                <span>Turnos de {asignacion.duracion_turno_minutos} minutos</span>}
            </li>)}
          </ul>}
        </section>
      </section>}
    </div>
  </ProfesionalShell>;
}

export default function PerfilPropio(props: PerfilPropioProps) {
  return props.tipo === "profesional"
    ? <PerfilProfesional {...props} />
    : <PerfilPaciente {...props} />;
}
