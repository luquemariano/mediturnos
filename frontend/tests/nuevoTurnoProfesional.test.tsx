import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import axios from "axios";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import NuevoTurnoProfesional from "../src/components/NuevoTurnoProfesional";
import * as pacienteService from "../src/services/pacienteService";
import * as prestacionService from "../src/services/prestacionService";
import * as turnoService from "../src/services/turnoService";
import type { Turno } from "../src/types/turno";

vi.mock("../src/services/pacienteService", () => ({ obtenerPacientesParaProfesional: vi.fn() }));
vi.mock("../src/services/prestacionService", () => ({ obtenerMisPrestaciones: vi.fn(), obtenerPrestaciones: vi.fn() }));
vi.mock("../src/services/turnoService", () => ({ crearMiTurnoProfesional: vi.fn(), obtenerHorariosLibres: vi.fn() }));

const propia = { id: 3, nombre: "Consulta", descripcion: null, duracion_minutos: 50, precio: 100, modalidad: "presencial" as const, activa: true, profesional_id: 7, especialidad_id: 1 };
const creado: Turno = { id: 9, paciente_id: 2, paciente_nombre: "Ana López", prestacion_id: 3, prestacion_nombre: "Consulta", profesional_nombre: "Sofía Ramírez", especialidad_nombre: "Clínica", fecha_hora: "2030-01-07T12:00:00Z", fecha_fin: "2030-01-07T12:50:00Z", estado: "reservado", observaciones: null };

function preparar() {
  vi.mocked(pacienteService.obtenerPacientesParaProfesional).mockResolvedValue([{ id: 2, nombre: "Ana", apellido: "López" }]);
  vi.mocked(prestacionService.obtenerMisPrestaciones).mockResolvedValue([propia, { ...propia, id: 5, nombre: "Inactiva", activa: false }]);
}

async function completarHastaFecha() {
  render(<NuevoTurnoProfesional onCerrar={vi.fn()} onCreado={vi.fn()} />);
  await screen.findByRole("option", { name: "López, Ana" });
  fireEvent.change(screen.getByLabelText("Paciente"), { target: { value: "2" } });
  fireEvent.change(screen.getByLabelText("Prestación"), { target: { value: "3" } });
  fireEvent.change(screen.getByLabelText("Fecha"), { target: { value: "2030-01-07" } });
}

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.setSystemTime(new Date("2026-08-24T20:30:00Z"));
  vi.clearAllMocks();
  preparar();
});

afterEach(() => vi.useRealTimers());

describe("nuevo turno profesional", () => {
  it("carga pacientes mínimos y muestra sólo prestaciones propias activas", async () => {
    render(<NuevoTurnoProfesional onCerrar={vi.fn()} onCreado={vi.fn()} />);
    expect(await screen.findByRole("option", { name: "López, Ana" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Consulta · 50 min" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: /Ajena/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("option", { name: /Inactiva/ })).not.toBeInTheDocument();
    expect(prestacionService.obtenerPrestaciones).not.toHaveBeenCalled();
  });

  it("consulta los slots del backend al elegir prestación y fecha", async () => {
    vi.mocked(turnoService.obtenerHorariosLibres).mockResolvedValue([{ fecha_hora: "2030-01-07T12:00:00Z" }]);
    await completarHastaFecha();
    expect(await screen.findByRole("radio", { name: "09:00" })).toBeInTheDocument();
    expect(turnoService.obtenerHorariosLibres).toHaveBeenCalledWith(3, "2030-01-07");
  });

  it("informa cuando no existen slots", async () => {
    vi.mocked(turnoService.obtenerHorariosLibres).mockResolvedValue([]);
    await completarHastaFecha();
    expect(await screen.findByText("No hay horarios disponibles para esta fecha.")).toBeInTheDocument();
  });

  it("mantiene habilitados todos los horarios de una fecha futura", async () => {
    vi.mocked(turnoService.obtenerHorariosLibres).mockResolvedValue([
      { fecha_hora: "2030-01-07T12:00:00Z" },
      { fecha_hora: "2030-01-07T12:30:00Z" },
    ]);

    await completarHastaFecha();

    expect(await screen.findByRole("radio", { name: "09:00" })).toBeEnabled();
    expect(screen.getByRole("radio", { name: "09:30" })).toBeEnabled();
  });

  it("deshabilita horarios anteriores o iguales a ahora y conserva los futuros", async () => {
    vi.mocked(turnoService.obtenerHorariosLibres).mockResolvedValue([
      { fecha_hora: "2026-08-24T19:30:00Z" },
      { fecha_hora: "2026-08-24T20:30:00Z" },
      { fecha_hora: "2026-08-24T21:00:00Z" },
    ]);
    render(<NuevoTurnoProfesional onCerrar={vi.fn()} onCreado={vi.fn()} />);
    await screen.findByRole("option", { name: "López, Ana" });
    fireEvent.change(screen.getByLabelText("Prestación"), { target: { value: "3" } });
    fireEvent.change(screen.getByLabelText("Fecha"), { target: { value: "2026-08-24" } });

    const anterior = await screen.findByRole("radio", { name: "16:30" });
    const igual = screen.getByRole("radio", { name: "17:30" });
    const futuro = screen.getByRole("radio", { name: "18:00" });
    expect(anterior).toBeDisabled();
    expect(igual).toBeDisabled();
    expect(anterior.closest("label")).toHaveClass("horario-pasado");
    expect(igual.closest("label")).toHaveClass("horario-pasado");
    expect(futuro).toBeEnabled();
    fireEvent.click(igual);
    expect(igual).not.toBeChecked();
  });

  it("impide fechas anteriores con min y bloquea un estado pasado forzado", async () => {
    vi.mocked(turnoService.obtenerHorariosLibres).mockResolvedValue([
      { fecha_hora: "2026-08-23T15:00:00Z" },
    ]);
    render(<NuevoTurnoProfesional onCerrar={vi.fn()} onCreado={vi.fn()} />);
    await screen.findByRole("option", { name: "López, Ana" });
    fireEvent.change(screen.getByLabelText("Paciente"), { target: { value: "2" } });
    fireEvent.change(screen.getByLabelText("Prestación"), { target: { value: "3" } });
    const selectorFecha = screen.getByLabelText("Fecha");
    expect(selectorFecha).toHaveAttribute("min", "2026-08-24");
    fireEvent.change(selectorFecha, { target: { value: "2026-08-23" } });

    expect(await screen.findByRole("radio", { name: "12:00" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Confirmar turno" })).toBeDisabled();
    expect(turnoService.crearMiTurnoProfesional).not.toHaveBeenCalled();
  });

  it("limpia la selección cuando una recarga deja el horario inválido", async () => {
    vi.mocked(turnoService.obtenerHorariosLibres)
      .mockResolvedValueOnce([{ fecha_hora: "2030-01-07T12:00:00Z" }])
      .mockResolvedValueOnce([{ fecha_hora: "2026-08-24T20:30:00Z" }]);
    await completarHastaFecha();
    fireEvent.click(await screen.findByRole("radio", { name: "09:00" }));
    expect(screen.getByRole("button", { name: "Confirmar turno" })).toBeEnabled();

    fireEvent.change(screen.getByLabelText("Fecha"), { target: { value: "2026-08-24" } });

    expect(await screen.findByRole("radio", { name: "17:30" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Confirmar turno" })).toBeDisabled();
  });

  it("crea sin profesional_id, bloquea doble submit y conserva observaciones", async () => {
    vi.mocked(turnoService.obtenerHorariosLibres).mockResolvedValue([{ fecha_hora: "2030-01-07T12:00:00Z" }]);
    let resolver!: (turno: Turno) => void;
    vi.mocked(turnoService.crearMiTurnoProfesional).mockReturnValue(new Promise((resolve) => { resolver = resolve; }));
    const onCreado = vi.fn();
    render(<NuevoTurnoProfesional onCerrar={vi.fn()} onCreado={onCreado} />);
    await screen.findByRole("option", { name: "López, Ana" });
    fireEvent.change(screen.getByLabelText("Paciente"), { target: { value: "2" } });
    fireEvent.change(screen.getByLabelText("Prestación"), { target: { value: "3" } });
    fireEvent.change(screen.getByLabelText("Fecha"), { target: { value: "2030-01-07" } });
    const horario = await screen.findByRole("radio", { name: "09:00" });
    fireEvent.click(horario);
    fireEvent.change(screen.getByLabelText(/Observaciones/), { target: { value: "Control" } });
    fireEvent.click(screen.getByRole("button", { name: "Confirmar turno" }));
    expect(screen.getByRole("button", { name: "Guardando…" })).toBeDisabled();
    fireEvent.submit(screen.getByRole("button", { name: "Guardando…" }).closest("form")!);
    expect(turnoService.crearMiTurnoProfesional).toHaveBeenCalledTimes(1);
    expect(turnoService.crearMiTurnoProfesional).toHaveBeenCalledWith(expect.not.objectContaining({ profesional_id: expect.anything() }));
    resolver(creado);
    await waitFor(() => expect(onCreado).toHaveBeenCalledWith(creado));
  });

  it("muestra el 409 y conserva los campos", async () => {
    vi.mocked(turnoService.obtenerHorariosLibres).mockResolvedValue([{ fecha_hora: "2030-01-07T12:00:00Z" }]);
    vi.mocked(turnoService.crearMiTurnoProfesional).mockRejectedValue(new axios.AxiosError("conflicto", "409", undefined, undefined, { status: 409, statusText: "Conflict", headers: {}, config: { headers: {} }, data: { detail: "El horario ya no está disponible." } }));
    await completarHastaFecha();
    fireEvent.click(await screen.findByRole("radio", { name: "09:00" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar turno" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("horario ya no está disponible");
    expect(screen.getByLabelText("Paciente")).toHaveValue("2");
    expect(screen.getByLabelText("Prestación")).toHaveValue("3");
    expect(screen.getByLabelText("Fecha")).toHaveValue("2030-01-07");
  });
});
