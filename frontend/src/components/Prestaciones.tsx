import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import axios from "axios";

import "./Prestaciones.css";
import ModalPrestacion from "./ModalPrestacion";
import { obtenerEspecialidades } from "../services/especialidadService";
import { obtenerPrestaciones } from "../services/prestacionService";
import { obtenerProfesionales } from "../services/profesionalService";
import type { Especialidad } from "../types/especialidad";
import type { Prestacion } from "../types/prestacion";
import type { Profesional } from "../types/profesional";


type PrestacionesProps = {
  onVolver: () => void;
};


function formatearPrecio(
  precio: number | string,
): string {
  const valor = Number(precio);

  if (!Number.isFinite(valor)) {
    return String(precio);
  }

  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency: "ARS",
    minimumFractionDigits: 2,
  }).format(valor);
}


function Prestaciones({
  onVolver,
}: PrestacionesProps) {
  const [prestaciones, setPrestaciones] =
    useState<Prestacion[]>([]);
  const [profesionales, setProfesionales] =
    useState<Profesional[]>([]);
  const [especialidades, setEspecialidades] =
    useState<Especialidad[]>([]);
  const [cargando, setCargando] =
    useState(true);
  const [mensajeError, setMensajeError] =
    useState("");
  const [mensajeExito, setMensajeExito] =
    useState("");
  const [mostrarFormulario, setMostrarFormulario] =
    useState(false);
  const [prestacionEnEdicion, setPrestacionEnEdicion] =
    useState<Prestacion | null>(null);

  const profesionalesPorId = useMemo(
    () => new Map(
      profesionales.map((profesional) => [
        profesional.id,
        profesional,
      ]),
    ),
    [profesionales],
  );

  const especialidadesPorId = useMemo(
    () => new Map(
      especialidades.map((especialidad) => [
        especialidad.id,
        especialidad,
      ]),
    ),
    [especialidades],
  );


  const cargarDatos = useCallback(async () => {
    setCargando(true);
    setMensajeError("");

    try {
      const [
        prestacionesObtenidas,
        profesionalesObtenidos,
        especialidadesObtenidas,
      ] = await Promise.all([
        obtenerPrestaciones(),
        obtenerProfesionales(),
        obtenerEspecialidades(),
      ]);

      setPrestaciones(prestacionesObtenidas);
      setProfesionales(profesionalesObtenidos);
      setEspecialidades(especialidadesObtenidas);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detalle = error.response?.data?.detail;

        setMensajeError(
          typeof detalle === "string"
            ? detalle
            : "No se pudieron cargar las prestaciones.",
        );
      } else {
        setMensajeError("Ocurrió un error inesperado.");
      }
    } finally {
      setCargando(false);
    }
  }, []);


  useEffect(() => {
    cargarDatos();
  }, [cargarDatos]);


  function manejarPrestacionGuardada(
    prestacion: Prestacion,
  ) {
    if (prestacionEnEdicion) {
      setPrestaciones((anteriores) =>
        anteriores.map((item) =>
          item.id === prestacion.id
            ? prestacion
            : item
        )
      );
      setMensajeExito(
        `${prestacion.nombre} fue actualizada correctamente.`,
      );
    } else {
      setPrestaciones((anteriores) => [
        prestacion,
        ...anteriores,
      ]);
      setMensajeExito(
        `${prestacion.nombre} fue registrada correctamente.`,
      );
    }

    setMostrarFormulario(false);
    setPrestacionEnEdicion(null);
  }


  function cerrarFormulario() {
    setMostrarFormulario(false);
    setPrestacionEnEdicion(null);
  }


  return (
    <main className="pagina-dashboard">
      <section className="dashboard">
        <header className="dashboard-encabezado">
          <div className="marca dashboard-marca">
            <span className="marca-icono">+</span>
            <div>
              <h1>MediTurnos</h1>
              <p>Gestión de prestaciones</p>
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

        <section className="prestaciones-contenido">
          <div className="prestaciones-cabecera">
            <div>
              <p className="prestaciones-etiqueta">
                Módulo
              </p>
              <h2>Prestaciones</h2>
              <p>
                Administrá los servicios ofrecidos por cada profesional.
              </p>
            </div>

            <button
              type="button"
              className="boton-primario"
              onClick={() => {
                setMensajeExito("");
                setPrestacionEnEdicion(null);
                setMostrarFormulario(true);
              }}
            >
              Nueva prestación
            </button>
          </div>

          {mensajeExito && (
            <p
              className="prestaciones-exito"
              role="status"
            >
              {mensajeExito}
            </p>
          )}

          {cargando && (
            <div className="prestaciones-estado">
              <span className="prestaciones-carga" />
              <p>Cargando prestaciones...</p>
            </div>
          )}

          {!cargando && mensajeError && (
            <div className="prestaciones-estado prestaciones-error">
              <p>{mensajeError}</p>
              <button
                type="button"
                className="boton-cerrar-sesion"
                onClick={cargarDatos}
              >
                Reintentar
              </button>
            </div>
          )}

          {!cargando
            && !mensajeError
            && prestaciones.length === 0
            && (
              <div className="prestaciones-vacio">
                <span>✚</span>
                <h3>No hay prestaciones registradas</h3>
                <p>
                  Creá la primera prestación para comenzar a ofrecer turnos.
                </p>
              </div>
            )}

          {!cargando
            && !mensajeError
            && prestaciones.length > 0
            && (
              <div className="tabla-prestaciones-contenedor">
                <table className="tabla-prestaciones">
                  <thead>
                    <tr>
                      <th>Prestación</th>
                      <th>Profesional</th>
                      <th>Especialidad</th>
                      <th>Duración</th>
                      <th>Precio</th>
                      <th>Estado</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>

                  <tbody>
                    {prestaciones.map((prestacion) => {
                      const profesional =
                        profesionalesPorId.get(
                          prestacion.profesional_id,
                        );
                      const especialidad =
                        especialidadesPorId.get(
                          prestacion.especialidad_id,
                        );

                      return (
                        <tr key={prestacion.id}>
                          <td>
                            <div className="prestacion-identidad">
                              <strong>{prestacion.nombre}</strong>
                              <span>
                                {prestacion.modalidad === "virtual"
                                  ? "Virtual"
                                  : "Presencial"}
                              </span>
                            </div>
                          </td>
                          <td>
                            {profesional
                              ? `${profesional.nombre} ${profesional.apellido}`
                              : `Profesional #${prestacion.profesional_id}`}
                          </td>
                          <td>
                            {especialidad?.nombre
                              ?? `Especialidad #${prestacion.especialidad_id}`}
                          </td>
                          <td>
                            {prestacion.duracion_minutos} minutos
                          </td>
                          <td>
                            {formatearPrecio(prestacion.precio)}
                          </td>
                          <td>
                            <span
                              className={
                                prestacion.activa
                                  ? "prestacion-activa"
                                  : "prestacion-inactiva"
                              }
                            >
                              {prestacion.activa
                                ? "Activa"
                                : "Inactiva"}
                            </span>
                          </td>
                          <td>
                            <button
                              type="button"
                              className="prestaciones-boton-editar"
                              onClick={() => {
                                setMensajeExito("");
                                setPrestacionEnEdicion(prestacion);
                                setMostrarFormulario(true);
                              }}
                            >
                              Editar
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
        </section>
      </section>

      {mostrarFormulario && (
        <ModalPrestacion
          prestacion={prestacionEnEdicion}
          profesionales={profesionales}
          especialidades={especialidades}
          onCerrar={cerrarFormulario}
          onPrestacionGuardada={manejarPrestacionGuardada}
        />
      )}
    </main>
  );
}

export default Prestaciones;
