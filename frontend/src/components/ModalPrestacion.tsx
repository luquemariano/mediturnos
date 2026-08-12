import { useMemo, useState } from "react";
import type {
  ChangeEvent,
  FormEvent,
} from "react";
import axios from "axios";

import {
  actualizarPrestacion,
  crearPrestacion,
} from "../services/prestacionService";
import type { Especialidad } from "../types/especialidad";
import type {
  ModalidadPrestacion,
  Prestacion,
  PrestacionActualizar,
  PrestacionCrear,
} from "../types/prestacion";
import type { Profesional } from "../types/profesional";


type ModalPrestacionProps = {
  prestacion?: Prestacion | null;
  profesionales: Profesional[];
  especialidades: Especialidad[];
  onCerrar: () => void;
  onPrestacionGuardada: (
    prestacion: Prestacion,
  ) => void;
};

type FormularioPrestacion = {
  nombre: string;
  descripcion: string;
  duracionMinutos: string;
  precio: string;
  modalidad: ModalidadPrestacion;
  profesionalId: string;
  especialidadId: string;
  activa: boolean;
};


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


function crearFormularioInicial(
  prestacion?: Prestacion | null,
): FormularioPrestacion {
  return {
    nombre: prestacion?.nombre ?? "",
    descripcion: prestacion?.descripcion ?? "",
    duracionMinutos: String(
      prestacion?.duracion_minutos ?? 30,
    ),
    precio: prestacion
      ? String(prestacion.precio)
      : "0",
    modalidad: prestacion?.modalidad ?? "presencial",
    profesionalId: prestacion
      ? String(prestacion.profesional_id)
      : "",
    especialidadId: prestacion
      ? String(prestacion.especialidad_id)
      : "",
    activa: prestacion?.activa ?? true,
  };
}


function ModalPrestacion({
  prestacion,
  profesionales,
  especialidades,
  onCerrar,
  onPrestacionGuardada,
}: ModalPrestacionProps) {
  const esEdicion = Boolean(prestacion);
  const [formulario, setFormulario] =
    useState<FormularioPrestacion>(
      () => crearFormularioInicial(prestacion),
    );
  const [guardando, setGuardando] =
    useState(false);
  const [mensajeError, setMensajeError] =
    useState("");

  const profesionalSeleccionado =
    profesionales.find(
      (profesional) =>
        profesional.id
        === Number(formulario.profesionalId),
    );

  const especialidadesDisponibles = useMemo(() => {
    if (!profesionalSeleccionado) {
      return [];
    }

    const idsAsignados = new Set(
      profesionalSeleccionado.especialidades.map(
        (asignacion) => asignacion.especialidad_id,
      ),
    );

    return especialidades.filter(
      (especialidad) =>
        idsAsignados.has(especialidad.id)
        && especialidad.activa,
    );
  }, [especialidades, profesionalSeleccionado]);


  function manejarCambio(
    evento: ChangeEvent<
      HTMLInputElement
      | HTMLTextAreaElement
      | HTMLSelectElement
    >,
  ) {
    const { name, value } = evento.target;

    setFormulario((anterior) => ({
      ...anterior,
      [name]: value,
    }));
  }


  function manejarCambioProfesional(
    evento: ChangeEvent<HTMLSelectElement>,
  ) {
    const profesionalId = evento.target.value;
    const profesional = profesionales.find(
      (item) => item.id === Number(profesionalId),
    );
    const especialidadesActivas =
      profesional?.especialidades
        .map((asignacion) => ({
          asignacion,
          especialidad: especialidades.find(
            (item) =>
              item.id === asignacion.especialidad_id
              && item.activa,
          ),
        }))
        .filter((item) => item.especialidad) ?? [];
    const primera = especialidadesActivas[0];

    setFormulario((anterior) => ({
      ...anterior,
      profesionalId,
      especialidadId: primera
        ? String(primera.asignacion.especialidad_id)
        : "",
      duracionMinutos: primera
        ? String(
          primera.asignacion.duracion_turno_minutos
          ?? primera.especialidad?.duracion_turno_minutos
          ?? 30,
        )
        : anterior.duracionMinutos,
    }));
  }


  function manejarCambioEspecialidad(
    evento: ChangeEvent<HTMLSelectElement>,
  ) {
    const especialidadId = evento.target.value;
    const asignacion =
      profesionalSeleccionado?.especialidades.find(
        (item) =>
          item.especialidad_id
          === Number(especialidadId),
      );
    const especialidad = especialidades.find(
      (item) => item.id === Number(especialidadId),
    );

    setFormulario((anterior) => ({
      ...anterior,
      especialidadId,
      duracionMinutos: especialidadId
        ? String(
          asignacion?.duracion_turno_minutos
          ?? especialidad?.duracion_turno_minutos
          ?? anterior.duracionMinutos,
        )
        : anterior.duracionMinutos,
    }));
  }


  async function manejarEnvio(
    evento: FormEvent<HTMLFormElement>,
  ) {
    evento.preventDefault();
    setMensajeError("");

    const nombre = formulario.nombre.trim();
    const descripcion = formulario.descripcion.trim();
    const duracionMinutos = Number(
      formulario.duracionMinutos,
    );
    const precio = Number(formulario.precio);
    const precioValido = /^\d+(\.\d{1,2})?$/.test(
      formulario.precio.trim(),
    );

    if (
      nombre.length < 2
      || !Number.isInteger(duracionMinutos)
      || duracionMinutos < 10
      || duracionMinutos > 240
      || !precioValido
      || precio < 0
    ) {
      setMensajeError(
        "Completá correctamente los campos obligatorios.",
      );
      return;
    }

    if (
      !esEdicion
      && (
        !formulario.profesionalId
        || !formulario.especialidadId
      )
    ) {
      setMensajeError(
        "Seleccioná un profesional con una especialidad asignada.",
      );
      return;
    }

    setGuardando(true);

    try {
      let prestacionGuardada: Prestacion;

      if (prestacion) {
        const cambios: PrestacionActualizar = {};

        if (nombre !== prestacion.nombre) {
          cambios.nombre = nombre;
        }

        if (
          descripcion !== (prestacion.descripcion ?? "")
        ) {
          cambios.descripcion = descripcion || null;
        }

        if (
          duracionMinutos !== prestacion.duracion_minutos
        ) {
          cambios.duracion_minutos = duracionMinutos;
        }

        if (precio !== Number(prestacion.precio)) {
          cambios.precio = precio;
        }

        if (formulario.modalidad !== prestacion.modalidad) {
          cambios.modalidad = formulario.modalidad;
        }

        if (formulario.activa !== prestacion.activa) {
          cambios.activa = formulario.activa;
        }

        prestacionGuardada =
          Object.keys(cambios).length > 0
            ? await actualizarPrestacion(
              prestacion.id,
              cambios,
            )
            : prestacion;
      } else {
        const datos: PrestacionCrear = {
          nombre,
          descripcion: descripcion || null,
          duracion_minutos: duracionMinutos,
          precio,
          modalidad: formulario.modalidad,
          profesional_id: Number(
            formulario.profesionalId,
          ),
          especialidad_id: Number(
            formulario.especialidadId,
          ),
        };

        prestacionGuardada =
          await crearPrestacion(datos);
      }

      onPrestacionGuardada(prestacionGuardada);
    } catch (error) {
      setMensajeError(
        obtenerMensajeError(
          error,
          esEdicion
            ? "No se pudo actualizar la prestación."
            : "No se pudo registrar la prestación.",
        ),
      );
    } finally {
      setGuardando(false);
    }
  }


  return (
    <div className="prestaciones-modal-fondo">
      <section
        className="prestaciones-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-modal-prestacion"
      >
        <header className="prestaciones-modal-encabezado">
          <div>
            <p className="prestaciones-modal-etiqueta">
              {esEdicion ? "Edición" : "Nuevo registro"}
            </p>
            <h2 id="titulo-modal-prestacion">
              {esEdicion
                ? "Editar prestación"
                : "Nueva prestación"}
            </h2>
            <p>
              Configurá los datos ofrecidos por el profesional.
            </p>
          </div>

          <button
            type="button"
            className="prestaciones-modal-cerrar"
            onClick={onCerrar}
            aria-label="Cerrar formulario"
            disabled={guardando}
          >
            ×
          </button>
        </header>

        <form
          className="formulario-prestacion"
          onSubmit={manejarEnvio}
        >
          <div className="formulario-prestacion-campos">
            <div className="prestaciones-campo prestaciones-campo-ancho">
              <label htmlFor="prestacion-nombre">
                Nombre *
              </label>
              <input
                id="prestacion-nombre"
                name="nombre"
                type="text"
                value={formulario.nombre}
                onChange={manejarCambio}
                minLength={2}
                maxLength={120}
                required
                autoFocus
              />
            </div>

            <div className="prestaciones-campo">
              <label htmlFor="prestacion-profesional">
                Profesional *
              </label>
              <select
                id="prestacion-profesional"
                name="profesionalId"
                value={formulario.profesionalId}
                onChange={manejarCambioProfesional}
                disabled={esEdicion}
                required
              >
                <option value="">
                  Seleccionar profesional
                </option>
                {profesionales
                  .filter((profesional) =>
                    profesional.activo || (
                      esEdicion
                      && profesional.id
                      === prestacion?.profesional_id
                    )
                  )
                  .map((profesional) => (
                    <option
                      key={profesional.id}
                      value={profesional.id}
                    >
                      {profesional.nombre} {profesional.apellido}
                    </option>
                  ))}
              </select>
            </div>

            <div className="prestaciones-campo">
              <label htmlFor="prestacion-especialidad">
                Especialidad *
              </label>
              <select
                id="prestacion-especialidad"
                name="especialidadId"
                value={formulario.especialidadId}
                onChange={manejarCambioEspecialidad}
                disabled={esEdicion || !profesionalSeleccionado}
                required
              >
                <option value="">
                  Seleccionar especialidad
                </option>
                {(esEdicion
                  ? especialidades.filter(
                    (especialidad) =>
                      especialidad.id
                      === prestacion?.especialidad_id,
                  )
                  : especialidadesDisponibles
                ).map((especialidad) => (
                  <option
                    key={especialidad.id}
                    value={especialidad.id}
                  >
                    {especialidad.nombre}
                  </option>
                ))}
              </select>
              {!esEdicion
                && profesionalSeleccionado
                && especialidadesDisponibles.length === 0
                && (
                  <small className="prestaciones-ayuda-error">
                    El profesional no tiene especialidades activas asignadas.
                  </small>
                )}
            </div>

            <div className="prestaciones-campo">
              <label htmlFor="prestacion-duracion">
                Duración (minutos) *
              </label>
              <input
                id="prestacion-duracion"
                name="duracionMinutos"
                type="number"
                value={formulario.duracionMinutos}
                onChange={manejarCambio}
                min={10}
                max={240}
                step={1}
                required
              />
            </div>

            <div className="prestaciones-campo">
              <label htmlFor="prestacion-precio">
                Precio *
              </label>
              <input
                id="prestacion-precio"
                name="precio"
                type="number"
                value={formulario.precio}
                onChange={manejarCambio}
                min={0}
                step="0.01"
                required
              />
            </div>

            <div className="prestaciones-campo">
              <label htmlFor="prestacion-modalidad">
                Modalidad *
              </label>
              <select
                id="prestacion-modalidad"
                name="modalidad"
                value={formulario.modalidad}
                onChange={manejarCambio}
                required
              >
                <option value="presencial">Presencial</option>
                <option value="virtual">Virtual</option>
              </select>
            </div>

            <div className="prestaciones-campo prestaciones-campo-ancho">
              <label htmlFor="prestacion-descripcion">
                Descripción
              </label>
              <textarea
                id="prestacion-descripcion"
                name="descripcion"
                value={formulario.descripcion}
                onChange={manejarCambio}
                rows={3}
                placeholder="Descripción opcional"
              />
            </div>

            {esEdicion && (
              <label className="prestaciones-estado-control">
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
                <span>Prestación activa</span>
              </label>
            )}
          </div>

          {mensajeError && (
            <p
              className="prestaciones-formulario-error"
              role="alert"
            >
              {mensajeError}
            </p>
          )}

          <footer className="prestaciones-modal-acciones">
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
                  : "Guardar prestación"}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

export default ModalPrestacion;
