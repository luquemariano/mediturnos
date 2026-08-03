import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import axios from "axios";

import "./Pacientes.css";
import ModalPaciente from "./ModalPaciente";
import type { Paciente } from "../types/paciente";
import { obtenerPacientes } from "../services/pacienteService";

type PacientesProps = {
  onVolver: () => void;
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

function Pacientes({
  onVolver,
}: PacientesProps) {
  const [pacientes, setPacientes] =
    useState<Paciente[]>([]);

  const [busqueda, setBusqueda] =
    useState("");

  const [cargando, setCargando] =
    useState(true);

  const [mensajeError, setMensajeError] =
    useState("");

  const [mensajeExito, setMensajeExito] =
    useState("");

  const [mostrarModal, setMostrarModal] =
    useState(false);

  const cargarPacientes =
    useCallback(async () => {
      setCargando(true);
      setMensajeError("");

      try {
        const datos = await obtenerPacientes();
        setPacientes(datos);
      } catch (error) {
        if (axios.isAxiosError(error)) {
          const detalle =
            error.response?.data?.detail;

          setMensajeError(
            typeof detalle === "string"
              ? detalle
              : "No se pudieron cargar los pacientes.",
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
    cargarPacientes();
  }, [cargarPacientes]);

  const pacientesFiltrados = useMemo(() => {
    const termino =
      normalizarTexto(busqueda);

    if (!termino) {
      return pacientes;
    }

    return pacientes.filter((paciente) => {
      const valoresPaciente = [
        paciente.nombre,
        paciente.apellido,
        `${paciente.nombre} ${paciente.apellido}`,
        paciente.dni,
        paciente.telefono,
        paciente.email,
        paciente.obra_social,
        paciente.numero_afiliado,
      ];

      return valoresPaciente.some((valor) =>
        normalizarTexto(valor).includes(termino),
      );
    });
  }, [busqueda, pacientes]);

  function abrirModal() {
    setMensajeExito("");
    setMostrarModal(true);
  }

  function cerrarModal() {
    setMostrarModal(false);
  }

  function limpiarBusqueda() {
    setBusqueda("");
  }

  function manejarPacienteCreado(
    paciente: Paciente,
  ) {
    setPacientes((pacientesAnteriores) => [
      ...pacientesAnteriores,
      paciente,
    ]);

    setMostrarModal(false);

    setMensajeExito(
      `Paciente ${paciente.nombre} ${paciente.apellido} registrado correctamente.`,
    );
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
              <h1>MediTurnos</h1>
              <p>Gestión de pacientes</p>
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

        <section className="pacientes-contenido">
          <div className="pacientes-cabecera">
            <div>
              <p className="pacientes-etiqueta">
                Módulo
              </p>

              <h2>Pacientes</h2>

              <p>
                Consultá y administrá la
                información registrada de los
                pacientes.
              </p>
            </div>

            <button
              type="button"
              className="boton-primario"
              onClick={abrirModal}
            >
              + Nuevo paciente
            </button>
          </div>

          {mensajeExito && (
            <p className="mensaje-pagina-exito">
              {mensajeExito}
            </p>
          )}

          {!cargando
            && !mensajeError
            && pacientes.length > 0
            && (
              <div className="pacientes-herramientas">
                <div className="buscador-pacientes">
                  <span
                    className="buscador-icono"
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
                    placeholder={
                      "Buscar por nombre, DNI, email u obra social"
                    }
                    aria-label="Buscar pacientes"
                  />

                  {busqueda && (
                    <button
                      type="button"
                      className="buscador-limpiar"
                      onClick={limpiarBusqueda}
                      aria-label="Limpiar búsqueda"
                    >
                      ×
                    </button>
                  )}
                </div>

                <p className="pacientes-contador">
                  {pacientesFiltrados.length}
                  {" "}
                  {pacientesFiltrados.length === 1
                    ? "paciente"
                    : "pacientes"}
                </p>
              </div>
            )}

          {cargando && (
            <div className="estado-pagina">
              <span className="indicador-carga" />
              <p>Cargando pacientes...</p>
            </div>
          )}

          {!cargando && mensajeError && (
            <div className="estado-pagina error-pagina">
              <p>{mensajeError}</p>

              <button
                type="button"
                className="boton-secundario"
                onClick={cargarPacientes}
              >
                Reintentar
              </button>
            </div>
          )}

          {!cargando
            && !mensajeError
            && pacientes.length === 0
            && (
              <div className="estado-vacio">
                <span>👥</span>

                <h3>
                  No hay pacientes registrados
                </h3>

                <p>
                  Registrá el primer paciente
                  para comenzar a gestionar sus
                  turnos.
                </p>

                <button
                  type="button"
                  className="boton-primario"
                  onClick={abrirModal}
                >
                  Registrar paciente
                </button>
              </div>
            )}

          {!cargando
            && !mensajeError
            && pacientes.length > 0
            && pacientesFiltrados.length === 0
            && (
              <div className="estado-vacio">
                <span>🔎</span>

                <h3>
                  No encontramos pacientes
                </h3>

                <p>
                  No hay resultados para
                  {" "}
                  <strong>
                    “{busqueda}”
                  </strong>
                  .
                </p>

                <button
                  type="button"
                  className="boton-secundario"
                  onClick={limpiarBusqueda}
                >
                  Limpiar búsqueda
                </button>
              </div>
            )}

          {!cargando
            && !mensajeError
            && pacientesFiltrados.length > 0
            && (
              <div className="tabla-contenedor">
                <table className="tabla-pacientes">
                  <thead>
                    <tr>
                      <th>Paciente</th>
                      <th>DNI</th>
                      <th>Teléfono</th>
                      <th>Obra social</th>
                      <th>Estado</th>
                    </tr>
                  </thead>

                  <tbody>
                    {pacientesFiltrados.map(
                      (paciente) => (
                        <tr key={paciente.id}>
                          <td>
                            <div className="paciente-identidad">
                              <span className="paciente-avatar">
                                {paciente.nombre
                                  .charAt(0)
                                  .toUpperCase()}
                              </span>

                              <div>
                                <strong>
                                  {paciente.nombre}
                                  {" "}
                                  {paciente.apellido}
                                </strong>

                                <span>
                                  {paciente.email
                                    || "Sin email"}
                                </span>
                              </div>
                            </div>
                          </td>

                          <td>
                            {paciente.dni}
                          </td>

                          <td>
                            {paciente.telefono}
                          </td>

                          <td>
                            {paciente.obra_social
                              || "Particular"}
                          </td>

                          <td>
                            <span
                              className={
                                paciente.activo
                                  ? "estado-activo"
                                  : "estado-inactivo"
                              }
                            >
                              {paciente.activo
                                ? "Activo"
                                : "Inactivo"}
                            </span>
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            )}
        </section>
      </section>

      {mostrarModal && (
        <ModalPaciente
          onCerrar={cerrarModal}
          onPacienteCreado={
            manejarPacienteCreado
          }
        />
      )}
    </main>
  );
}

export default Pacientes;