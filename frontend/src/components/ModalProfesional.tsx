import {
  useCallback,
  useEffect,
  useState,
} from "react";
import type {
  ChangeEvent,
  FormEvent,
} from "react";
import axios from "axios";

import { obtenerEspecialidades } from "../services/especialidadService";
import {
  actualizarProfesional,
  crearProfesional,
} from "../services/profesionalService";
import type { Especialidad } from "../types/especialidad";
import type {
  Profesional,
  ProfesionalActualizar,
  ProfesionalCrear,
  EspecialidadProfesionalCrear,
} from "../types/profesional";


type ModalProfesionalProps = {
  onCerrar: () => void;
  onProfesionalGuardado: (
    profesional: Profesional,
  ) => void;
  profesional?: Profesional | null;
};

type FormularioProfesional = {
  nombre: string;
  apellido: string;
  matricula: string;
  email: string;
  telefono: string;
  especialidadId: string;
  duracionTurnoMinutos: string;
};

type EspecialidadEditada = {
  especialidadId: string;
  duracionTurnoMinutos: string;
};

function crearFormularioInicial(
  profesional?: Profesional | null,
): FormularioProfesional {
  return {
    nombre: profesional?.nombre ?? "",
    apellido: profesional?.apellido ?? "",
    matricula: profesional?.matricula ?? "",
    email: profesional?.email ?? "",
    telefono: profesional?.telefono ?? "",
    especialidadId: "",
    duracionTurnoMinutos: "",
  };
}


function crearEspecialidadesIniciales(
  profesional?: Profesional | null,
): EspecialidadEditada[] {
  return (profesional?.especialidades ?? []).map(
    (especialidad) => ({
      especialidadId: String(
        especialidad.especialidad_id,
      ),
      duracionTurnoMinutos:
        especialidad.duracion_turno_minutos
          === null
          ? ""
          : String(
            especialidad.duracion_turno_minutos,
          ),
    }),
  );
}


function firmaEspecialidades(
  especialidades: EspecialidadEditada[],
): string {
  return especialidades
    .map((especialidad) => (
      `${especialidad.especialidadId}:`
      + especialidad.duracionTurnoMinutos
    ))
    .sort()
    .join("|");
}


function obtenerMensajeError(
  error: unknown,
  mensajePredeterminado: string,
): string {
  if (!axios.isAxiosError(error)) {
    return "Ocurrió un error inesperado.";
  }

  const detalle = error.response?.data?.detail;

  if (typeof detalle === "string") {
    return detalle;
  }

  if (Array.isArray(detalle)) {
    const mensajes = detalle
      .map((item) => item?.msg)
      .filter((mensaje): mensaje is string =>
        typeof mensaje === "string"
      );

    if (mensajes.length > 0) {
      return mensajes.join(" ");
    }
  }

  return mensajePredeterminado;
}


function ModalProfesional({
  onCerrar,
  onProfesionalGuardado,
  profesional,
}: ModalProfesionalProps) {
  const esEdicion = Boolean(profesional);

  const [formulario, setFormulario] =
    useState<FormularioProfesional>(
      () => crearFormularioInicial(profesional),
    );

  const [especialidades, setEspecialidades] =
    useState<Especialidad[]>([]);

  const [especialidadesEditadas,
    setEspecialidadesEditadas] =
    useState<EspecialidadEditada[]>(
      () => crearEspecialidadesIniciales(
        profesional,
      ),
    );

  const [cargandoEspecialidades,
    setCargandoEspecialidades] = useState(true);

  const [guardando, setGuardando] =
    useState(false);

  const [mensajeError, setMensajeError] =
    useState("");


  const cargarEspecialidades =
    useCallback(async () => {
      setCargandoEspecialidades(true);
      setMensajeError("");

      try {
        const datos =
          await obtenerEspecialidades();

        setEspecialidades(datos);
      } catch (error) {
        setMensajeError(
          obtenerMensajeError(
            error,
            "No se pudieron cargar las especialidades.",
          ),
        );
      } finally {
        setCargandoEspecialidades(false);
      }
    }, []);


  useEffect(() => {
    cargarEspecialidades();
  }, [cargarEspecialidades]);


  function manejarCambio(
    evento: ChangeEvent<
      HTMLInputElement | HTMLSelectElement
    >,
  ) {
    const { name, value } = evento.target;

    if (name === "especialidadId") {
      const especialidad = especialidades.find(
        (item) => item.id === Number(value),
      );

      setFormulario((datosAnteriores) => ({
        ...datosAnteriores,
        especialidadId: value,
        duracionTurnoMinutos: especialidad
          ? String(
            especialidad.duracion_turno_minutos,
          )
          : "",
      }));
      return;
    }

    setFormulario((datosAnteriores) => ({
      ...datosAnteriores,
      [name]: value,
    }));
  }


  function agregarEspecialidad() {
    const idsSeleccionados = new Set(
      especialidadesEditadas.map(
        (item) => Number(item.especialidadId),
      ),
    );
    const especialidadDisponible =
      especialidades.find(
        (item) =>
          item.activa
          && !idsSeleccionados.has(item.id),
      );

    if (!especialidadDisponible) {
      return;
    }

    setEspecialidadesEditadas((anteriores) => [
      ...anteriores,
      {
        especialidadId: String(
          especialidadDisponible.id,
        ),
        duracionTurnoMinutos: String(
          especialidadDisponible
            .duracion_turno_minutos,
        ),
      },
    ]);
  }


  function quitarEspecialidad(indice: number) {
    setEspecialidadesEditadas((anteriores) =>
      anteriores.filter(
        (_, posicion) => posicion !== indice,
      )
    );
  }


  function cambiarEspecialidadEditada(
    indice: number,
    campo: keyof EspecialidadEditada,
    valor: string,
  ) {
    setEspecialidadesEditadas((anteriores) =>
      anteriores.map((item, posicion) => {
        if (posicion !== indice) {
          return item;
        }

        if (campo === "especialidadId") {
          const especialidad = especialidades.find(
            (opcion) => opcion.id === Number(valor),
          );

          return {
            especialidadId: valor,
            duracionTurnoMinutos: especialidad
              ? String(
                especialidad.duracion_turno_minutos,
              )
              : "",
          };
        }

        return {
          ...item,
          [campo]: valor,
        };
      })
    );
  }


  async function manejarEnvio(
    evento: FormEvent<HTMLFormElement>,
  ) {
    evento.preventDefault();
    setMensajeError("");

    const nombre = formulario.nombre.trim();
    const apellido = formulario.apellido.trim();
    const matricula = formulario.matricula.trim();
    const email = formulario.email.trim();
    const telefono = formulario.telefono.trim();
    const especialidadId = Number(
      formulario.especialidadId,
    );
    const duracionTurnoMinutos = Number(
      formulario.duracionTurnoMinutos,
    );

    if (
      nombre.length < 2
      || apellido.length < 2
      || matricula.length < 3
    ) {
      setMensajeError(
        "Completá correctamente todos los campos obligatorios.",
      );
      return;
    }

    if (
      !esEdicion
      && (
        !Number.isInteger(especialidadId)
        || especialidadId <= 0
        || !Number.isInteger(duracionTurnoMinutos)
        || duracionTurnoMinutos < 10
        || duracionTurnoMinutos > 180
      )
    ) {
      setMensajeError(
        "Completá correctamente todos los campos obligatorios.",
      );
      return;
    }

    if (
      email
      && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
    ) {
      setMensajeError(
        "Ingresá un correo electrónico válido.",
      );
      return;
    }

    let especialidadesActualizadas:
      EspecialidadProfesionalCrear[] | undefined;

    if (profesional) {
      const especialidadesOriginales =
        crearEspecialidadesIniciales(profesional);
      const especialidadesCambiaron =
        firmaEspecialidades(especialidadesEditadas)
        !== firmaEspecialidades(
          especialidadesOriginales,
        );

      if (especialidadesCambiaron) {
        const ids = especialidadesEditadas.map(
          (item) => Number(item.especialidadId),
        );
        const duraciones = especialidadesEditadas.map(
          (item) => Number(
            item.duracionTurnoMinutos,
          ),
        );
        const especialidadesValidas =
          especialidadesEditadas.length > 0
          && ids.every(
            (id) => Number.isInteger(id) && id > 0,
          )
          && new Set(ids).size === ids.length
          && duraciones.every(
            (duracion) =>
              Number.isInteger(duracion)
              && duracion >= 10
              && duracion <= 180,
          );

        if (!especialidadesValidas) {
          setMensajeError(
            "Agregá al menos una especialidad y revisá sus duraciones.",
          );
          return;
        }

        especialidadesActualizadas =
          especialidadesEditadas.map(
            (_, indice) => ({
              especialidad_id: ids[indice],
              duracion_turno_minutos:
                duraciones[indice],
            }),
          );
      }
    }

    setGuardando(true);

    try {
      let profesionalGuardado: Profesional;

      if (profesional) {
        const cambios: ProfesionalActualizar = {};

        if (nombre !== profesional.nombre) {
          cambios.nombre = nombre;
        }

        if (apellido !== profesional.apellido) {
          cambios.apellido = apellido;
        }

        if (matricula !== profesional.matricula) {
          cambios.matricula = matricula;
        }

        if (email !== (profesional.email ?? "")) {
          cambios.email = email || null;
        }

        if (
          telefono !== (profesional.telefono ?? "")
        ) {
          cambios.telefono = telefono || null;
        }

        if (especialidadesActualizadas) {
          cambios.especialidades =
            especialidadesActualizadas;
        }

        profesionalGuardado =
          await actualizarProfesional(
            profesional.id,
            cambios,
          );
      } else {
        const datos: ProfesionalCrear = {
          nombre,
          apellido,
          matricula,
          ...(telefono ? { telefono } : {}),
          ...(email ? { email } : {}),
          especialidades: [
            {
              especialidad_id: especialidadId,
              duracion_turno_minutos:
                duracionTurnoMinutos,
            },
          ],
        };

        profesionalGuardado =
          await crearProfesional(datos);
      }

      onProfesionalGuardado(
        profesionalGuardado,
      );
    } catch (error) {
      setMensajeError(
        obtenerMensajeError(
          error,
          esEdicion
            ? "No se pudo actualizar el profesional. Revisá los datos ingresados."
            : "No se pudo registrar el profesional. Revisá los datos ingresados.",
        ),
      );
    } finally {
      setGuardando(false);
    }
  }


  return (
    <div
      className="modal-fondo"
      role="presentation"
    >
      <section
        className="modal-profesional"
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-modal-profesional"
      >
        <header className="modal-encabezado">
          <div>
            <p className="modal-etiqueta">
              {esEdicion
                ? "Edición"
                : "Nuevo registro"}
            </p>

            <h2 id="titulo-modal-profesional">
              {esEdicion
                ? "Editar profesional"
                : "Nuevo profesional"}
            </h2>

            <p>
              {esEdicion
                ? "Actualizá sus datos y especialidades asignadas."
                : "Completá los datos requeridos para registrar al profesional."}
            </p>
          </div>

          <button
            type="button"
            className="modal-cerrar"
            onClick={onCerrar}
            aria-label="Cerrar formulario"
            disabled={guardando}
          >
            ×
          </button>
        </header>

        <form
          className="formulario-profesional"
          onSubmit={manejarEnvio}
        >
          <div className="formulario-grilla">
            <div className="campo-formulario">
              <label htmlFor="profesional-nombre">
                Nombre *
              </label>

              <input
                id="profesional-nombre"
                name="nombre"
                type="text"
                value={formulario.nombre}
                onChange={manejarCambio}
                minLength={2}
                maxLength={100}
                required
                autoFocus
              />
            </div>

            <div className="campo-formulario">
              <label htmlFor="profesional-apellido">
                Apellido *
              </label>

              <input
                id="profesional-apellido"
                name="apellido"
                type="text"
                value={formulario.apellido}
                onChange={manejarCambio}
                minLength={2}
                maxLength={100}
                required
              />
            </div>

            <div className="campo-formulario">
              <label htmlFor="profesional-matricula">
                Matrícula *
              </label>

              <input
                id="profesional-matricula"
                name="matricula"
                type="text"
                value={formulario.matricula}
                onChange={manejarCambio}
                minLength={3}
                maxLength={50}
                required
              />
            </div>

            {!esEdicion && (
              <div className="campo-formulario">
                <label htmlFor="profesional-especialidad">
                  Especialidad *
                </label>

                <select
                  id="profesional-especialidad"
                  name="especialidadId"
                  value={formulario.especialidadId}
                  onChange={manejarCambio}
                  disabled={
                    cargandoEspecialidades
                    || guardando
                  }
                  required
                >
                  <option value="">
                    {cargandoEspecialidades
                      ? "Cargando especialidades..."
                      : "Seleccioná una especialidad"}
                  </option>

                  {especialidades
                    .filter((especialidad) =>
                      especialidad.activa
                    )
                    .map(
                    (especialidad) => (
                      <option
                        key={especialidad.id}
                        value={especialidad.id}
                      >
                        {especialidad.nombre}
                      </option>
                    ),
                  )}
                </select>
              </div>
            )}

            <div className="campo-formulario">
              <label htmlFor="profesional-email">
                Email
              </label>

              <input
                id="profesional-email"
                name="email"
                type="email"
                value={formulario.email}
                onChange={manejarCambio}
                maxLength={150}
                placeholder="nombre@ejemplo.com"
              />
            </div>

            <div className="campo-formulario">
              <label htmlFor="profesional-telefono">
                Teléfono
              </label>

              <input
                id="profesional-telefono"
                name="telefono"
                type="tel"
                value={formulario.telefono}
                onChange={manejarCambio}
                maxLength={30}
                placeholder="Ejemplo: +54 11 5555-1234"
              />
            </div>

            {!esEdicion && (
              <div className="campo-formulario">
                <label htmlFor="profesional-duracion">
                  Duración del turno (minutos) *
                </label>

                <input
                  id="profesional-duracion"
                  name="duracionTurnoMinutos"
                  type="number"
                  value={
                    formulario.duracionTurnoMinutos
                  }
                  onChange={manejarCambio}
                  min={10}
                  max={180}
                  step={1}
                  disabled={guardando}
                  required
                />
              </div>
            )}

            {esEdicion && (
              <section className="editor-especialidades-profesional">
                <header className="editor-especialidades-encabezado">
                  <div>
                    <h3>Especialidades</h3>
                    <p>
                      Administrá las especialidades y
                      la duración de sus turnos.
                    </p>
                  </div>

                  <button
                    type="button"
                    className="boton-secundario"
                    onClick={agregarEspecialidad}
                    disabled={
                      guardando
                      || cargandoEspecialidades
                      || !especialidades.some(
                        (especialidad) =>
                          especialidad.activa
                          && !especialidadesEditadas
                            .some(
                              (item) =>
                                Number(
                                  item.especialidadId,
                                ) === especialidad.id,
                            ),
                      )
                    }
                  >
                    Agregar especialidad
                  </button>
                </header>

                <div className="editor-especialidades-lista">
                  {especialidadesEditadas.map(
                    (item, indice) => (
                      <div
                        className="editor-especialidad-fila"
                        key={`${item.especialidadId}-${indice}`}
                      >
                        <div className="campo-formulario">
                          <label
                            htmlFor={`especialidad-editada-${indice}`}
                          >
                            Especialidad *
                          </label>

                          <select
                            id={`especialidad-editada-${indice}`}
                            value={item.especialidadId}
                            onChange={(evento) =>
                              cambiarEspecialidadEditada(
                                indice,
                                "especialidadId",
                                evento.target.value,
                              )
                            }
                            disabled={
                              guardando
                              || cargandoEspecialidades
                            }
                            required
                          >
                            {especialidades
                              .filter((especialidad) =>
                                (
                                  especialidad.activa
                                  || especialidad.id
                                    === Number(
                                      item.especialidadId,
                                    )
                                )
                                && !especialidadesEditadas
                                  .some(
                                    (seleccionada,
                                      posicion) =>
                                      posicion !== indice
                                      && Number(
                                        seleccionada
                                          .especialidadId,
                                      ) === especialidad.id,
                                  )
                              )
                              .map((especialidad) => (
                                <option
                                  key={especialidad.id}
                                  value={especialidad.id}
                                >
                                  {especialidad.nombre}
                                </option>
                              ))}
                          </select>
                        </div>

                        <div className="campo-formulario">
                          <label
                            htmlFor={`duracion-editada-${indice}`}
                          >
                            Duración (minutos) *
                          </label>

                          <input
                            id={`duracion-editada-${indice}`}
                            type="number"
                            value={
                              item.duracionTurnoMinutos
                            }
                            onChange={(evento) =>
                              cambiarEspecialidadEditada(
                                indice,
                                "duracionTurnoMinutos",
                                evento.target.value,
                              )
                            }
                            min={10}
                            max={180}
                            step={1}
                            disabled={guardando}
                            required
                          />
                        </div>

                        <button
                          type="button"
                          className="editor-especialidad-quitar"
                          onClick={() =>
                            quitarEspecialidad(indice)
                          }
                          disabled={
                            guardando
                            || especialidadesEditadas.length
                              === 1
                          }
                        >
                          Quitar
                        </button>
                      </div>
                    ),
                  )}
                </div>
              </section>
            )}
          </div>

          {!esEdicion
            && !cargandoEspecialidades
            && !especialidades.some(
              (especialidad) => especialidad.activa,
            )
            && !mensajeError
            && (
              <p className="mensaje-formulario-error">
                No hay especialidades activas
                disponibles para el alta.
              </p>
            )}

          {mensajeError && (
            <p
              className="mensaje-formulario-error"
              role="alert"
            >
              {mensajeError}
            </p>
          )}

          <footer className="modal-acciones">
            <button
              type="button"
              className="boton-secundario"
              onClick={onCerrar}
              disabled={guardando}
            >
              Cancelar
            </button>

            <button
              type="submit"
              className="boton-primario"
              disabled={
                guardando
                || cargandoEspecialidades
                || (esEdicion
                  ? especialidades.length === 0
                  : !especialidades.some(
                    (especialidad) =>
                      especialidad.activa,
                  ))
              }
            >
              {guardando
                ? "Guardando..."
                : esEdicion
                  ? "Guardar cambios"
                  : "Guardar profesional"}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

export default ModalProfesional;
