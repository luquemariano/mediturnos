import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import AgendaPropia from "../src/components/AgendaPropia";
import * as servicio from "../src/services/turnoService";

vi.mock("../src/services/turnoService", () => ({
  obtenerMiAgendaProfesional: vi.fn(),
  obtenerMisTurnosPaciente: vi.fn(),
  cancelarMiTurno: vi.fn(),
  finalizarMiTurno: vi.fn(),
  marcarAusenteMiTurno: vi.fn(),
}));

beforeEach(() => vi.clearAllMocks());

it("el profesional carga únicamente su agenda propia", async () => {
  vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue([]);
  render(<AgendaPropia tipo="profesional" onVolver={vi.fn()} />);
  await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledOnce());
  expect(servicio.obtenerMisTurnosPaciente).not.toHaveBeenCalled();
  expect(screen.getByRole("heading", { name: "Mi agenda" })).toBeInTheDocument();
});

it("el paciente carga únicamente sus turnos propios", async () => {
  vi.mocked(servicio.obtenerMisTurnosPaciente).mockResolvedValue([]);
  render(<AgendaPropia tipo="paciente" onVolver={vi.fn()} />);
  await waitFor(() => expect(servicio.obtenerMisTurnosPaciente).toHaveBeenCalledOnce());
  expect(servicio.obtenerMiAgendaProfesional).not.toHaveBeenCalled();
  expect(screen.getByRole("heading", { name: "Mis turnos" })).toBeInTheDocument();
});
