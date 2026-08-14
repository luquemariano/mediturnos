import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import axios from "axios";

import "./Turnos.css";
import ModalNuevoTurno from "./ModalNuevoTurno";
import ModalReprogramarTurno from "./ModalReprogramarTurno";
import {
  cambiarEstadoTurno,
  obtenerTurnos,
} from "../services/turnoService";
import type {
  EstadoTurno,
  Turno,
} from "../types/turno";
import {
  claveFechaNegocio,
  formatearFechaAgrupada,
  formatearHoraTurno,
} from "../utils/fechaTurno";


type TurnosProps = {
  onVolver: () => void;
  rol: string;
};


type FiltroEstado =
  | "todos"
  | EstadoTurno;


const filtros: {
  valor: FiltroEstado;
  etiqueta: string;
}[] = [
  {
    valor: "todos",
    etiqueta: "Todos",
  },
  {
    valor: "reservado",
    etiqueta: "Reservados",
  },
  {
    valor: "confirmado",
    etiqueta: "Confirmados",
  },
  {
    valor: "finalizado",
    etiqueta: "Finalizados",
  },
  {
    valor: "cancelado",
    etiqueta: "Cancelados",
  },
  {
    valor: "ausente",
    etiqueta: "Ausentes",
  },
];


function normalizarTexto(
  texto: string | null,
): string {
  return (texto ?? "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}


function formatearHora(
  fechaHora: string,
): string {
  return formatearHoraTurno(fechaHora);
}


function formatearEstado(
  estado: EstadoTurno,
): string {
  const etiquetas: Record<
    EstadoTurno,
    string
  > = {
    reservado: "Reservado",
    confirmado: "Confirmado",
    cancelado: "Cancelado",
    ausente: "Ausente",
    finalizado: "Finalizado",
  };

  return etiquetas[estado];
}


function agruparTurnosPorFecha(
  turnos: Turno[],
): Record<string, Turno[]> {
  return turnos.reduce(
    (
      grupos: Record<string, Turno[]>,
      turno,
    ) => {
      const clave = claveFechaNegocio(
        turno.fecha_hora,
      );

      if (!grupos[clave]) {
        grupos[clave] = [];
      }

      grupos[clave].push(turno);

      return grupos;
    },
    {},
  );
}


function Turnos({
  onVolver,
  rol,
}: TurnosProps) {
  const [turnos, setTurnos] =
    useState<Turno[]>([]);

  const [busqueda, setBusqueda] =
    useState("");

  const [filtroEstado, setFiltroEstado] =
    useState<FiltroEstado>("todos");

  const [cargando, setCargando] =
    useState(true);

  const [mensajeError, setMensajeError] =
    useState("");

  const [mensajeExito, setMensajeExito] =
    useState("");

  const [turnoActualizando, setTurnoActualizando] =
    useState<number | null>(null);

  const [mostrarNuevoTurno, setMostrarNuevoTurno] =
    useState(false);

  const [turnoAReprogramar, setTurnoAReprogramar] =
    useState<Turno | null>(null);


  const cargarTurnos =
    useCallback(async () => {
      setCargando(true);
      setMensajeError("");

      try {
        const datos =
          await obtenerTurnos();

        setTurnos(datos);
      } catch (error) {
        if (axios.isAxiosError(error)) {
          const detalle =
            error.response?.data?.detail;

          setMensajeError(
            typeof detalle === "string"
              ? detalle
              : "No se pudo cargar la agenda.",
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
    cargarTurnos();
  }, [cargarTurnos]);


  const turnosFiltrados =
    useMemo(() => {
      const termino =
        normalizarTexto(busqueda);

      return turnos.filter((turno) => {
        const coincideEstado =
          filtroEstado === "todos"
          || turno.estado === filtroEstado;

        const valores = [
          turno.paciente_nombre,
          turno.prestacion_nombre,
          turno.profesional_nombre,
          turno.especialidad_nombre,
          turno.observaciones,
        ];

        const coincideBusqueda =
          !termino
          || valores.some((valor) =>
            normalizarTexto(
              valor,
            ).includes(termino),
          );

        return (
          coincideEstado
          && coincideBusqueda
        );
      });
    }, [
      busqueda,
      filtroEstado,
      turnos,
    ]);


  const turnosAgrupados =
    useMemo(
      () =>
        agruparTurnosPorFecha(
          turnosFiltrados,
        ),
      [turnosFiltrados],
    );


  async function actualizarEstado(
    turno: Turno,
    nuevoEstado: EstadoTurno,
  ) {
    setMensajeError("");
    setMensajeExito("");
    setTurnoActualizando(turno.id);

    try {
      const turnoActualizado =
        await cambiarEstadoTurno(
          turno.id,
          nuevoEstado,
        );

      setTurnos(
        (turnosAnteriores) =>
          turnosAnteriores.map(
            (turnoExistente) =>
              turnoExistente.id
                === turnoActualizado.id
                ? turnoActualizado
                : turnoExistente,
          ),
      );

      setMensajeExito(
        `El turno de ${turno.paciente_nombre} fue actualizado correctamente.`,
      );
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detalle =
          error.response?.data?.detail;

        setMensajeError(
          typeof detalle === "string"
            ? detalle
            : "No se pudo actualizar el turno.",
        );
      } else {
        setMensajeError(
          "Ocurrió un error inesperado.",
        );
      }
    } finally {
      setTurnoActualizando(null);
    }
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
              <p>Agenda médica</p>
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

        <section className="turnos-contenido">
          <div className="turnos-cabecera">
            <div>
              <p className="turnos-etiqueta">
                Agenda
              </p>

              <h2>
                Turnos médicos
              </h2>

              <p>
                Consultá la agenda y gestioná
                el estado de cada turno.
              </p>
            </div>

            <div className="turnos-cabecera-acciones">
              {["administrador", "recepcionista"].includes(rol) && (
                <button
                  type="button"
                  className="boton-primario"
                  onClick={() => {
                    setMensajeError("");
                    setMensajeExito("");
                    setMostrarNuevoTurno(true);
                  }}
                >
                  Nuevo turno
                </button>
              )}

              <div className="turnos-resumen">
              <strong>
                {turnosFiltrados.length}
              </strong>

              <span>
                {turnosFiltrados.length === 1
                  ? "turno visible"
                  : "turnos visibles"}
                </span>
              </div>
            </div>
          </div>

          <div className="turnos-herramientas">
            <div className="buscador-turnos">
              <span aria-hidden="true">
                🔎
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
                  "Buscar paciente, profesional o especialidad"
                }
                aria-label="Buscar turnos"
              />
            </div>

            <div className="filtros-turnos">
              {filtros.map((filtro) => (
                <button
                  key={filtro.valor}
                  type="button"
                  className={
                    filtroEstado
                      === filtro.valor
                      ? "filtro-turno activo"
                      : "filtro-turno"
                  }
                  onClick={() =>
                    setFiltroEstado(
                      filtro.valor,
                    )
                  }
                >
                  {filtro.etiqueta}
                </button>
              ))}
            </div>
          </div>

          {mensajeExito && (
            <p className="mensaje-turnos-exito">
              {mensajeExito}
            </p>
          )}

          {mensajeError && (
            <p className="mensaje-turnos-error">
              {mensajeError}
            </p>
          )}

          {cargando && (
            <div className="agenda-estado">
              <span className="indicador-carga" />
              <p>Cargando agenda...</p>
            </div>
          )}

          {!cargando
            && !mensajeError
            && turnos.length === 0
            && (
              <div className="agenda-estado">
                <span className="agenda-vacio-icono">
                  📅
                </span>

                <h3>
                  No hay turnos registrados
                </h3>

                <p>
                  Los turnos aparecerán acá
                  cuando sean creados.
                </p>
              </div>
            )}

          {!cargando
            && turnos.length > 0
            && turnosFiltrados.length === 0
            && (
              <div className="agenda-estado">
                <span className="agenda-vacio-icono">
                  🔍
                </span>

                <h3>
                  No encontramos resultados
                </h3>

                <p>
                  Probá con otra búsqueda o
                  cambiá el filtro seleccionado.
                </p>
              </div>
            )}

          {!cargando
            && turnosFiltrados.length > 0
            && (
              <div className="agenda-grupos">
                {Object.entries(
                  turnosAgrupados,
                ).map(
                  ([
                    fecha,
                    turnosDelDia,
                  ]) => (
                    <section
                      key={fecha}
                      className="agenda-dia"
                    >
                      <header className="agenda-dia-encabezado">
                        <div>
                          <span>
                            {fecha
                              .split("-")
                              .reverse()
                              .slice(0, 2)
                              .join("/")}
                          </span>

                          <h3>
                            {formatearFechaAgrupada(fecha)}
                          </h3>
                        </div>

                        <small>
                          {turnosDelDia.length}
                          {" "}
                          {turnosDelDia.length === 1
                            ? "turno"
                            : "turnos"}
                        </small>
                      </header>

                      <div className="agenda-lista">
                        {turnosDelDia.map(
                          (turno) => (
                            <article
                              key={turno.id}
                              className={
                                `turno-tarjeta estado-${turno.estado}`
                              }
                            >
                              <div className="turno-hora">
                                <strong>
                                  {formatearHora(
                                    turno.fecha_hora,
                                  )}
                                </strong>

                                <span>
                                  Turno #{turno.id}
                                </span>
                              </div>

                              <div className="turno-informacion">
                                <div className="turno-paciente">
                                  <span className="turno-avatar">
                                    {turno.paciente_nombre
                                      .charAt(0)
                                      .toUpperCase()}
                                  </span>

                                  <div>
                                    <h4>
                                      {
                                        turno.paciente_nombre
                                      }
                                    </h4>

                                    <p>
                                      {
                                        turno.prestacion_nombre
                                      }
                                    </p>
                                  </div>
                                </div>

                                <div className="turno-detalles">
                                  <p>
                                    <span>
                                      Profesional
                                    </span>

                                    <strong>
                                      {
                                        turno.profesional_nombre
                                      }
                                    </strong>
                                  </p>

                                  <p>
                                    <span>
                                      Especialidad
                                    </span>

                                    <strong>
                                      {
                                        turno.especialidad_nombre
                                      }
                                    </strong>
                                  </p>
                                </div>

                                {turno.observaciones && (
                                  <p className="turno-observaciones">
                                    {
                                      turno.observaciones
                                    }
                                  </p>
                                )}
                              </div>

                              <div className="turno-acciones">
                                <span
                                  className={
                                    `turno-badge badge-${turno.estado}`
                                  }
                                >
                                  {formatearEstado(
                                    turno.estado,
                                  )}
                                </span>

                                {turno.estado
                                  === "reservado"
                                  && (
                                    <button
                                      type="button"
                                      className="accion-confirmar"
                                      disabled={
                                        turnoActualizando
                                        === turno.id
                                      }
                                      onClick={() =>
                                        actualizarEstado(
                                          turno,
                                          "confirmado",
                                        )
                                      }
                                    >
                                      Confirmar
                                    </button>
                                  )}

                                {["administrador", "recepcionista"].includes(rol)
                                  && turno.estado
                                  !== "cancelado"
                                  && turno.estado
                                  !== "finalizado"
                                  && (
                                    <button
                                      type="button"
                                      className="accion-reprogramar"
                                      disabled={turnoActualizando === turno.id}
                                      onClick={() => {
                                        setMensajeError("");
                                        setMensajeExito("");
                                        setTurnoAReprogramar(turno);
                                      }}
                                    >
                                      Reprogramar
                                    </button>
                                  )}

                                {turno.estado
                                  !== "cancelado"
                                  && turno.estado
                                  !== "finalizado"
                                  && (
                                    <button
                                      type="button"
                                      className="accion-cancelar"
                                      disabled={
                                        turnoActualizando
                                        === turno.id
                                      }
                                      onClick={() =>
                                        actualizarEstado(
                                          turno,
                                          "cancelado",
                                        )
                                      }
                                    >
                                      Cancelar
                                    </button>
                                  )}
                              </div>
                            </article>
                          ),
                        )}
                      </div>
                    </section>
                  ),
                )}
              </div>
            )}
        </section>
      </section>

      {mostrarNuevoTurno && (
        <ModalNuevoTurno
          onCerrar={() => setMostrarNuevoTurno(false)}
          onTurnoCreado={(turno) => {
            setTurnos((actuales) => [...actuales, turno]);
            setMostrarNuevoTurno(false);
            setMensajeExito(
              `El turno de ${turno.paciente_nombre} fue creado correctamente.`,
            );
          }}
        />
      )}

      {turnoAReprogramar
        && ["administrador", "recepcionista"].includes(rol)
        && (
          <ModalReprogramarTurno
            turno={turnoAReprogramar}
            onCerrar={() => setTurnoAReprogramar(null)}
            onTurnoReprogramado={(turnoActualizado) => {
              setTurnos((actuales) => actuales.map((turno) =>
                turno.id === turnoActualizado.id
                  ? turnoActualizado
                  : turno
              ));
              setTurnoAReprogramar(null);
              setMensajeExito(
                `El turno de ${turnoActualizado.paciente_nombre} fue reprogramado correctamente.`,
              );
            }}
          />
        )}
    </main>
  );
}

export default Turnos;
