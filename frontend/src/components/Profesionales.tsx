import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import axios from "axios";

import "./Profesionales.css";
import ModalProfesional from "./ModalProfesional";
import { obtenerProfesionales } from "../services/profesionalService";
import type { Profesional } from "../types/profesional";


type ProfesionalesProps = {
  onVolver: () => void;
  rol: string;
};


function normalizarTexto(
  texto: string | null,
): string {
  return (texto ?? "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}


function Profesionales({
  onVolver,
  rol,
}: ProfesionalesProps) {
  const [profesionales, setProfesionales] =
    useState<Profesional[]>([]);

  const [busqueda, setBusqueda] =
    useState("");

  const [cargando, setCargando] =
    useState(true);

  const [mensajeError, setMensajeError] =
    useState("");

  const [mostrarFormulario,
    setMostrarFormulario] = useState(false);

  const [mensajeExito, setMensajeExito] =
    useState("");

  const [profesionalEnEdicion,
    setProfesionalEnEdicion] =
    useState<Profesional | null>(null);


  const cargarProfesionales =
    useCallback(async () => {
      setCargando(true);
      setMensajeError("");

      try {
        const datos =
          await obtenerProfesionales();

        setProfesionales(datos);
      } catch (error) {
        if (axios.isAxiosError(error)) {
          const detalle =
            error.response?.data?.detail;

          setMensajeError(
            typeof detalle === "string"
              ? detalle
              : "No se pudieron cargar los profesionales.",
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
    cargarProfesionales();
  }, [cargarProfesionales]);


  const profesionalesFiltrados =
    useMemo(() => {
      const termino =
        normalizarTexto(busqueda);

      if (!termino) {
        return profesionales;
      }

      return profesionales.filter(
        (profesional) => {
          const valores = [
            profesional.nombre,
            profesional.apellido,
            `${profesional.nombre} ${profesional.apellido}`,
            profesional.matricula,
          ];

          return valores.some((valor) =>
            normalizarTexto(valor).includes(
              termino,
            ),
          );
        },
      );
    }, [busqueda, profesionales]);


  function limpiarBusqueda() {
    setBusqueda("");
  }


  function manejarProfesionalGuardado(
    profesional: Profesional,
  ) {
    if (profesionalEnEdicion) {
      setProfesionales((datosAnteriores) =>
        datosAnteriores.map((item) =>
          item.id === profesional.id
            ? profesional
            : item
        )
      );
      setMensajeExito(
        `${profesional.nombre} ${profesional.apellido} fue actualizado correctamente.`,
      );
    } else {
      setProfesionales((datosAnteriores) => [
        profesional,
        ...datosAnteriores,
      ]);
      setBusqueda("");
      setMensajeExito(
        `${profesional.nombre} ${profesional.apellido} fue registrado correctamente.`,
      );
    }

    setMostrarFormulario(false);
    setProfesionalEnEdicion(null);
  }


  return (
    <main className="pagina-dashboard">
      <section className="dashboard">
        <header className="dashboard-encabezado">
          <div className="marca dashboard-marca">
            <span className="marca-icono">
              +
            </span>

            <div>
              <h1>Turnelia</h1>
              <p>Gestión de profesionales</p>
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

        <section className="profesionales-contenido">
          <div className="profesionales-cabecera">
            <div>
              <p className="profesionales-etiqueta">
                Módulo
              </p>

              <h2>Profesionales</h2>

              <p>
                Consultá el equipo profesional,
                sus datos de contacto y matrícula.
              </p>
            </div>

            {rol === "administrador" && (
              <button
                type="button"
                className="boton-primario"
                onClick={() => {
                  setMensajeExito("");
                  setProfesionalEnEdicion(null);
                  setMostrarFormulario(true);
                }}
              >
                Nuevo profesional
              </button>
            )}
          </div>

          {mensajeExito && (
            <p
              className="profesionales-exito"
              role="status"
            >
              {mensajeExito}
            </p>
          )}

          {!cargando
            && !mensajeError
            && profesionales.length > 0
            && (
              <div className="profesionales-herramientas">
                <div className="buscador-profesionales">
                  <span
                    className="buscador-profesionales-icono"
                    aria-hidden="true"
                  >
                    ⌕
                  </span>

                  <input
                    type="search"
                    value={busqueda}
                    onChange={(evento) =>
                      setBusqueda(
                        evento.target.value,
                      )
                    }
                    placeholder="Buscar por nombre, apellido o matrícula"
                    aria-label="Buscar profesionales"
                  />

                  {busqueda && (
                    <button
                      type="button"
                      className="buscador-profesionales-limpiar"
                      onClick={limpiarBusqueda}
                      aria-label="Limpiar búsqueda"
                    >
                      ×
                    </button>
                  )}
                </div>

                <p className="profesionales-contador">
                  {profesionalesFiltrados.length}
                  {" "}
                  {profesionalesFiltrados.length
                    === 1
                    ? "profesional"
                    : "profesionales"}
                </p>
              </div>
            )}

          {cargando && (
            <div className="profesionales-estado">
              <span className="profesionales-carga" />
              <p>Cargando profesionales...</p>
            </div>
          )}

          {!cargando && mensajeError && (
            <div className="profesionales-estado profesionales-error">
              <p>{mensajeError}</p>

              <button
                type="button"
                className="boton-cerrar-sesion"
                onClick={cargarProfesionales}
              >
                Reintentar
              </button>
            </div>
          )}

          {!cargando
            && !mensajeError
            && profesionales.length === 0
            && (
              <div className="profesionales-vacio">
                <span>🩺</span>

                <h3>
                  No hay profesionales registrados
                </h3>

                <p>
                  Los profesionales aparecerán acá
                  cuando sean registrados.
                </p>
              </div>
            )}

          {!cargando
            && !mensajeError
            && profesionales.length > 0
            && profesionalesFiltrados.length === 0
            && (
              <div className="profesionales-vacio">
                <span>🔎</span>

                <h3>
                  No encontramos profesionales
                </h3>

                <p>
                  No hay resultados para{" "}
                  <strong>“{busqueda}”</strong>.
                </p>

                <button
                  type="button"
                  className="boton-cerrar-sesion"
                  onClick={limpiarBusqueda}
                >
                  Limpiar búsqueda
                </button>
              </div>
            )}

          {!cargando
            && !mensajeError
            && profesionalesFiltrados.length > 0
            && (
              <div className="tabla-profesionales-contenedor">
                <table className="tabla-profesionales">
                  <thead>
                    <tr>
                      <th>Profesional</th>
                      <th>Matrícula</th>
                      <th>Teléfono</th>
                      <th>Estado</th>
                      {rol === "administrador" && (
                        <th>Acciones</th>
                      )}
                    </tr>
                  </thead>

                  <tbody>
                    {profesionalesFiltrados.map(
                      (profesional) => (
                        <tr key={profesional.id}>
                          <td>
                            <div className="profesional-identidad">
                              <span className="profesional-avatar">
                                {profesional.nombre
                                  .charAt(0)
                                  .toUpperCase()}
                              </span>

                              <div>
                                <strong>
                                  {profesional.nombre}
                                  {" "}
                                  {profesional.apellido}
                                </strong>

                                <span>
                                  {profesional.email
                                    || "Sin email"}
                                </span>
                              </div>
                            </div>
                          </td>

                          <td>
                            {profesional.matricula}
                          </td>

                          <td>
                            {profesional.telefono
                              || "Sin teléfono"}
                          </td>

                          <td>
                            <span
                              className={
                                profesional.activo
                                  ? "profesional-activo"
                                  : "profesional-inactivo"
                              }
                            >
                              {profesional.activo
                                ? "Activo"
                                : "Inactivo"}
                            </span>
                          </td>

                          {rol === "administrador" && (
                            <td>
                              <button
                                type="button"
                                className="profesionales-boton-editar"
                                onClick={() => {
                                  setMensajeExito("");
                                  setProfesionalEnEdicion(
                                    profesional,
                                  );
                                  setMostrarFormulario(true);
                                }}
                              >
                                Editar
                              </button>
                            </td>
                          )}
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            )}
        </section>
      </section>

      {mostrarFormulario && (
        <ModalProfesional
          profesional={profesionalEnEdicion}
          onCerrar={() => {
            setMostrarFormulario(false);
            setProfesionalEnEdicion(null);
          }}
          onProfesionalGuardado={
            manejarProfesionalGuardado
          }
        />
      )}
    </main>
  );
}

export default Profesionales;
