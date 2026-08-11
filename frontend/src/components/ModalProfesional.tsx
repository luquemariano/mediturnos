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
import { crearProfesional } from "../services/profesionalService";
import type { Especialidad } from "../types/especialidad";
import type {
  Profesional,
  ProfesionalCrear,
} from "../types/profesional";


type ModalProfesionalProps = {
  onCerrar: () => void;
  onProfesionalCreado: (
    profesional: Profesional,
  ) => void;
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

const formularioInicial: FormularioProfesional = {
  nombre: "",
  apellido: "",
  matricula: "",
  email: "",
  telefono: "",
  especialidadId: "",
  duracionTurnoMinutos: "",
};


function obtenerMensajeError(
  error: unknown,
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

  return "No se pudo registrar el profesional. Revisá los datos ingresados.";
}


function ModalProfesional({
  onCerrar,
  onProfesionalCreado,
}: ModalProfesionalProps) {
  const [formulario, setFormulario] =
    useState<FormularioProfesional>(
      formularioInicial,
    );

  const [especialidades, setEspecialidades] =
    useState<Especialidad[]>([]);

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

        setEspecialidades(
          datos.filter((especialidad) =>
            especialidad.activa
          ),
        );
      } catch (error) {
        setMensajeError(
          obtenerMensajeError(error),
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
      || !Number.isInteger(especialidadId)
      || especialidadId <= 0
      || !Number.isInteger(duracionTurnoMinutos)
      || duracionTurnoMinutos < 10
      || duracionTurnoMinutos > 180
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

    setGuardando(true);

    try {
      const profesionalCreado =
        await crearProfesional(datos);

      onProfesionalCreado(profesionalCreado);
    } catch (error) {
      setMensajeError(
        obtenerMensajeError(error),
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
              Nuevo registro
            </p>

            <h2 id="titulo-modal-profesional">
              Nuevo profesional
            </h2>

            <p>
              Completá los datos requeridos para
              registrar al profesional.
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

                {especialidades.map(
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
          </div>

          {!cargandoEspecialidades
            && especialidades.length === 0
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
                || especialidades.length === 0
              }
            >
              {guardando
                ? "Guardando..."
                : "Guardar profesional"}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

export default ModalProfesional;
