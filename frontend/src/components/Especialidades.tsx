import {
  useCallback,
  useEffect,
  useState,
} from "react";
import axios from "axios";

import "./Especialidades.css";
import ModalEspecialidad from "./ModalEspecialidad";
import { obtenerEspecialidades } from "../services/especialidadService";
import type { Especialidad } from "../types/especialidad";


type EspecialidadesProps = {
  onVolver: () => void;
};


function Especialidades({
  onVolver,
}: EspecialidadesProps) {
  const [especialidades, setEspecialidades] =
    useState<Especialidad[]>([]);
  const [cargando, setCargando] =
    useState(true);
  const [mensajeError, setMensajeError] =
    useState("");
  const [mensajeExito, setMensajeExito] =
    useState("");
  const [mostrarFormulario,
    setMostrarFormulario] = useState(false);
  const [especialidadEnEdicion,
    setEspecialidadEnEdicion] =
    useState<Especialidad | null>(null);


  const cargarEspecialidades =
    useCallback(async () => {
      setCargando(true);
      setMensajeError("");

      try {
        setEspecialidades(
          await obtenerEspecialidades(),
        );
      } catch (error) {
        if (axios.isAxiosError(error)) {
          const detalle = error.response?.data?.detail;

          setMensajeError(
            typeof detalle === "string"
              ? detalle
              : "No se pudieron cargar las especialidades.",
          );
        } else {
          setMensajeError(
            "Ocurrió un error inesperado.",
          );
        }
      } finally {
        setCargando(false);
      }
    }, []);


  useEffect(() => {
    cargarEspecialidades();
  }, [cargarEspecialidades]);


  function manejarEspecialidadGuardada(
    especialidad: Especialidad,
  ) {
    if (especialidadEnEdicion) {
      setEspecialidades((anteriores) =>
        anteriores.map((item) =>
          item.id === especialidad.id
            ? especialidad
            : item
        )
      );
      setMensajeExito(
        `${especialidad.nombre} fue actualizada correctamente.`,
      );
    } else {
      setEspecialidades((anteriores) => [
        ...anteriores,
        especialidad,
      ]);
      setMensajeExito(
        `${especialidad.nombre} fue registrada correctamente.`,
      );
    }

    setMostrarFormulario(false);
    setEspecialidadEnEdicion(null);
  }


  function cerrarFormulario() {
    setMostrarFormulario(false);
    setEspecialidadEnEdicion(null);
  }


  return (
    <main className="pagina-dashboard">
      <section className="dashboard">
        <header className="dashboard-encabezado">
          <div className="marca dashboard-marca">
            <span className="marca-icono">+</span>

            <div>
              <h1>MediTurnos</h1>
              <p>Gestión de especialidades</p>
            </div>
          </div>

          <button
            type="button"
            className="boton-cerrar-sesion"
            onClick={onVolver}
          >
            Volver al panel
          </button>
        </header>

        <section className="especialidades-contenido">
          <div className="especialidades-cabecera">
            <div>
              <p className="especialidades-etiqueta">
                Módulo
              </p>
              <h2>Especialidades</h2>
              <p>
                Administrá el catálogo y sus duraciones
                predeterminadas.
              </p>
            </div>

            <button
              type="button"
              className="boton-primario"
              onClick={() => {
                setMensajeExito("");
                setEspecialidadEnEdicion(null);
                setMostrarFormulario(true);
              }}
            >
              Nueva especialidad
            </button>
          </div>

          {mensajeExito && (
            <p
              className="especialidades-exito"
              role="status"
            >
              {mensajeExito}
            </p>
          )}

          {cargando && (
            <div className="especialidades-estado">
              <span className="especialidades-carga" />
              <p>Cargando especialidades...</p>
            </div>
          )}

          {!cargando && mensajeError && (
            <div className="especialidades-estado especialidades-error">
              <p>{mensajeError}</p>
              <button
                type="button"
                className="boton-cerrar-sesion"
                onClick={cargarEspecialidades}
              >
                Reintentar
              </button>
            </div>
          )}

          {!cargando
            && !mensajeError
            && especialidades.length === 0
            && (
              <div className="especialidades-vacio">
                <span>✦</span>
                <h3>No hay especialidades registradas</h3>
                <p>
                  Creá la primera especialidad para
                  comenzar a configurar el catálogo.
                </p>
              </div>
            )}

          {!cargando
            && !mensajeError
            && especialidades.length > 0
            && (
              <div className="tabla-especialidades-contenedor">
                <table className="tabla-especialidades">
                  <thead>
                    <tr>
                      <th>Especialidad</th>
                      <th>Duración predeterminada</th>
                      <th>Estado</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>

                  <tbody>
                    {especialidades.map((especialidad) => (
                      <tr key={especialidad.id}>
                        <td>
                          <div className="especialidad-identidad">
                            <strong>{especialidad.nombre}</strong>
                            <span>
                              {especialidad.descripcion
                                || "Sin descripción"}
                            </span>
                          </div>
                        </td>
                        <td>
                          {especialidad.duracion_turno_minutos}
                          {" minutos"}
                        </td>
                        <td>
                          <span
                            className={
                              especialidad.activa
                                ? "especialidad-activa"
                                : "especialidad-inactiva"
                            }
                          >
                            {especialidad.activa
                              ? "Activa"
                              : "Inactiva"}
                          </span>
                        </td>
                        <td>
                          <button
                            type="button"
                            className="especialidades-boton-editar"
                            onClick={() => {
                              setMensajeExito("");
                              setEspecialidadEnEdicion(
                                especialidad,
                              );
                              setMostrarFormulario(true);
                            }}
                          >
                            Editar
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
        </section>
      </section>

      {mostrarFormulario && (
        <ModalEspecialidad
          especialidad={especialidadEnEdicion}
          onCerrar={cerrarFormulario}
          onEspecialidadGuardada={
            manejarEspecialidadGuardada
          }
        />
      )}
    </main>
  );
}

export default Especialidades;
