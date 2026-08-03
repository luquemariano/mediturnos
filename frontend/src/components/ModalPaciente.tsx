import { useState } from "react";
import type {
  ChangeEvent,
  FormEvent,
} from "react";
import axios from "axios";

import { crearPaciente } from "../services/pacienteService";
import type {
  Paciente,
  PacienteCrear,
} from "../types/paciente";

type ModalPacienteProps = {
  onCerrar: () => void;
  onPacienteCreado: (
    paciente: Paciente,
  ) => void;
};

type FormularioPaciente = {
  nombre: string;
  apellido: string;
  dni: string;
  fecha_nacimiento: string;
  telefono: string;
  email: string;
  obra_social: string;
  numero_afiliado: string;
};

const formularioInicial: FormularioPaciente = {
  nombre: "",
  apellido: "",
  dni: "",
  fecha_nacimiento: "",
  telefono: "",
  email: "",
  obra_social: "",
  numero_afiliado: "",
};

function ModalPaciente({
  onCerrar,
  onPacienteCreado,
}: ModalPacienteProps) {
  const [formulario, setFormulario] =
    useState<FormularioPaciente>(
      formularioInicial,
    );

  const [guardando, setGuardando] =
    useState(false);

  const [mensajeError, setMensajeError] =
    useState("");

  function manejarCambio(
    evento: ChangeEvent<HTMLInputElement>,
  ) {
    const { name, value } = evento.target;

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
    setGuardando(true);

    const datos: PacienteCrear = {
      nombre: formulario.nombre.trim(),
      apellido: formulario.apellido.trim(),
      dni: formulario.dni.trim(),
      fecha_nacimiento:
        formulario.fecha_nacimiento || null,
      telefono: formulario.telefono.trim(),
      email:
        formulario.email.trim() || null,
      obra_social:
        formulario.obra_social.trim() || null,
      numero_afiliado:
        formulario.numero_afiliado.trim()
        || null,
    };

    try {
      const pacienteCreado =
        await crearPaciente(datos);

      onPacienteCreado(pacienteCreado);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const detalle =
          error.response?.data?.detail;

        if (typeof detalle === "string") {
          setMensajeError(detalle);
        } else {
          setMensajeError(
            "No se pudo registrar el paciente. Revisá los datos ingresados.",
          );
        }
      } else {
        setMensajeError(
          "Ocurrió un error inesperado.",
        );
      }
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
        className="modal-paciente"
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-modal-paciente"
      >
        <header className="modal-encabezado">
          <div>
            <p className="modal-etiqueta">
              Nuevo registro
            </p>

            <h2 id="titulo-modal-paciente">
              Nuevo paciente
            </h2>

            <p>
              Completá la información necesaria
              para registrar al paciente.
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
          className="formulario-paciente"
          onSubmit={manejarEnvio}
        >
          <div className="formulario-grilla">
            <div className="campo-formulario">
              <label htmlFor="nombre">
                Nombre *
              </label>

              <input
                id="nombre"
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
              <label htmlFor="apellido">
                Apellido *
              </label>

              <input
                id="apellido"
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
              <label htmlFor="dni">
                DNI *
              </label>

              <input
                id="dni"
                name="dni"
                type="text"
                value={formulario.dni}
                onChange={manejarCambio}
                minLength={7}
                maxLength={20}
                inputMode="numeric"
                required
              />
            </div>

            <div className="campo-formulario">
              <label htmlFor="fecha_nacimiento">
                Fecha de nacimiento
              </label>

              <input
                id="fecha_nacimiento"
                name="fecha_nacimiento"
                type="date"
                value={
                  formulario.fecha_nacimiento
                }
                onChange={manejarCambio}
              />
            </div>

            <div className="campo-formulario">
              <label htmlFor="telefono">
                Teléfono *
              </label>

              <input
                id="telefono"
                name="telefono"
                type="tel"
                value={formulario.telefono}
                onChange={manejarCambio}
                minLength={6}
                maxLength={30}
                required
              />
            </div>

            <div className="campo-formulario">
              <label htmlFor="email">
                Correo electrónico
              </label>

              <input
                id="email"
                name="email"
                type="email"
                value={formulario.email}
                onChange={manejarCambio}
                maxLength={150}
              />
            </div>

            <div className="campo-formulario">
              <label htmlFor="obra_social">
                Obra social
              </label>

              <input
                id="obra_social"
                name="obra_social"
                type="text"
                value={formulario.obra_social}
                onChange={manejarCambio}
                maxLength={100}
                placeholder="Ejemplo: PAMI"
              />
            </div>

            <div className="campo-formulario">
              <label htmlFor="numero_afiliado">
                Número de afiliado
              </label>

              <input
                id="numero_afiliado"
                name="numero_afiliado"
                type="text"
                value={
                  formulario.numero_afiliado
                }
                onChange={manejarCambio}
                maxLength={50}
              />
            </div>
          </div>

          {mensajeError && (
            <p className="mensaje-formulario-error">
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
                : "Guardar paciente"}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

export default ModalPaciente;