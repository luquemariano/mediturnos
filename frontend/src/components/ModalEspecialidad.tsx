import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import type {
  ChangeEvent,
  FormEvent,
} from "react";
import axios from "axios";

import {
  actualizarEspecialidad,
  crearEspecialidad,
} from "../services/especialidadService";
import type {
  Especialidad,
  EspecialidadActualizar,
  EspecialidadCrear,
} from "../types/especialidad";


type ModalEspecialidadProps = {
  especialidad?: Especialidad | null;
  onCerrar: () => void;
  onEspecialidadGuardada: (
    especialidad: Especialidad,
  ) => void;
};

type FormularioEspecialidad = {
  nombre: string;
  descripcion: string;
  duracionTurnoMinutos: string;
  activa: boolean;
};


function crearFormularioInicial(
  especialidad?: Especialidad | null,
): FormularioEspecialidad {
  return {
    nombre: especialidad?.nombre ?? "",
    descripcion: especialidad?.descripcion ?? "",
    duracionTurnoMinutos: String(
      especialidad?.duracion_turno_minutos ?? 30,
    ),
    activa: especialidad?.activa ?? true,
  };
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


function ModalEspecialidad({
  especialidad,
  onCerrar,
  onEspecialidadGuardada,
}: ModalEspecialidadProps) {
  const esEdicion = Boolean(especialidad);
  const [formulario, setFormulario] =
    useState<FormularioEspecialidad>(
      () => crearFormularioInicial(especialidad),
    );
  const [guardando, setGuardando] =
    useState(false);
  const [mensajeError, setMensajeError] =
    useState("");

  useEffect(() => {
    const posicionScroll = window.scrollY;
    const overflowAnterior = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = overflowAnterior;
      try {
        window.scrollTo(0, posicionScroll);
      } catch {
        // jsdom does not implement scrollTo; browsers restore the position above.
      }
    };
  }, []);


  function manejarCambio(
    evento: ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement
    >,
  ) {
    const { name, value } = evento.target;

    setFormulario((anterior) => ({
      ...anterior,
      [name]: value,
    }));
  }


  async function manejarEnvio(
    evento: FormEvent<HTMLFormElement>,
  ) {
    evento.preventDefault();
    setMensajeError("");

    const nombre = formulario.nombre.trim();
    const descripcion = formulario.descripcion.trim();
    const duracionTurnoMinutos = Number(
      formulario.duracionTurnoMinutos,
    );

    if (
      nombre.length < 2
      || !Number.isInteger(duracionTurnoMinutos)
      || duracionTurnoMinutos < 10
      || duracionTurnoMinutos > 180
    ) {
      setMensajeError(
        "Completá correctamente los campos obligatorios.",
      );
      return;
    }

    setGuardando(true);

    try {
      let especialidadGuardada: Especialidad;

      if (especialidad) {
        const cambios: EspecialidadActualizar = {};

        if (nombre !== especialidad.nombre) {
          cambios.nombre = nombre;
        }

        if (
          descripcion
          !== (especialidad.descripcion ?? "")
        ) {
          cambios.descripcion = descripcion || null;
        }

        if (
          duracionTurnoMinutos
          !== especialidad.duracion_turno_minutos
        ) {
          cambios.duracion_turno_minutos =
            duracionTurnoMinutos;
        }

        if (formulario.activa !== especialidad.activa) {
          cambios.activa = formulario.activa;
        }

        especialidadGuardada =
          await actualizarEspecialidad(
            especialidad.id,
            cambios,
          );
      } else {
        const datos: EspecialidadCrear = {
          nombre,
          descripcion: descripcion || null,
          duracion_turno_minutos:
            duracionTurnoMinutos,
        };

        especialidadGuardada =
          await crearEspecialidad(datos);
      }

      onEspecialidadGuardada(
        especialidadGuardada,
      );
    } catch (error) {
      setMensajeError(
        obtenerMensajeError(
          error,
          esEdicion
            ? "No se pudo actualizar la especialidad."
            : "No se pudo registrar la especialidad.",
        ),
      );
    } finally {
      setGuardando(false);
    }
  }


  return createPortal((
    <div
      className="modal-overlay modal-overlay-especialidad"
      role="presentation"
      onMouseDown={(evento) => {
        if (evento.target === evento.currentTarget && !guardando) onCerrar();
      }}
    >
      <section
        className="modal-especialidad"
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-modal-especialidad"
      >
        <header className="modal-encabezado">
          <div>
            <p className="modal-etiqueta">
              {esEdicion ? "Edición" : "Nuevo registro"}
            </p>

            <h2 id="titulo-modal-especialidad">
              {esEdicion
                ? "Editar especialidad"
                : "Nueva especialidad"}
            </h2>

            <p>
              Configurá los datos generales y la
              duración predeterminada de los turnos.
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
          className="formulario-especialidad"
          onSubmit={manejarEnvio}
        >
          <div className="formulario-especialidad-campos">
            <div className="campo-formulario">
              <label htmlFor="especialidad-nombre">
                Nombre *
              </label>

              <input
                id="especialidad-nombre"
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
              <label htmlFor="especialidad-duracion">
                Duración predeterminada (minutos) *
              </label>

              <input
                id="especialidad-duracion"
                name="duracionTurnoMinutos"
                type="number"
                value={formulario.duracionTurnoMinutos}
                onChange={manejarCambio}
                min={10}
                max={180}
                step={1}
                required
              />
            </div>

            <div className="campo-formulario campo-formulario-ancho">
              <label htmlFor="especialidad-descripcion">
                Descripción
              </label>

              <textarea
                id="especialidad-descripcion"
                name="descripcion"
                value={formulario.descripcion}
                onChange={manejarCambio}
                rows={4}
                placeholder="Descripción opcional"
              />
            </div>

            {esEdicion && (
              <label className="especialidad-estado-control">
                <input
                  type="checkbox"
                  checked={formulario.activa}
                  onChange={(evento) =>
                    setFormulario((anterior) => ({
                      ...anterior,
                      activa: evento.target.checked,
                    }))
                  }
                />

                <span>
                  Especialidad activa
                </span>
              </label>
            )}
          </div>

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
              disabled={guardando}
            >
              {guardando
                ? "Guardando..."
                : esEdicion
                  ? "Guardar cambios"
                  : "Guardar especialidad"}
            </button>
          </footer>
        </form>
      </section>
    </div>
  ), document.body);
}

export default ModalEspecialidad;
