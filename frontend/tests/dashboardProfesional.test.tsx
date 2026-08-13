import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import DashboardProfesional from "../src/components/DashboardProfesional";
import * as disponibilidadService from "../src/services/disponibilidadService";
import * as profesionalService from "../src/services/profesionalService";
import * as turnoService from "../src/services/turnoService";
import type { Turno } from "../src/types/turno";

vi.mock("../src/services/disponibilidadService", () => ({
  obtenerDisponibilidadesProfesional: vi.fn(),
}));
vi.mock("../src/services/profesionalService", () => ({
  obtenerMiPerfilProfesional: vi.fn(),
}));
vi.mock("../src/services/turnoService", () => ({
  obtenerMiAgendaProfesional: vi.fn(),
  finalizarMiTurno: vi.fn(),
  marcarAusenteMiTurno: vi.fn(),
}));

const perfil = {
  id: 7,
  nombre: "Mariana",
  apellido: "López",
  matricula: "MP-100",
  telefono: null,
  email: "mariana@example.com",
  activo: true,
  especialidades: [],
};

function turno(datos: Partial<Turno> = {}): Turno {
  return {
    id: 1,
    paciente_id: 4,
    paciente_nombre: "Lucía Fernández",
    prestacion_id: 5,
    prestacion_nombre: "Consulta psicológica",
    profesional_nombre: "Mariana López",
    especialidad_nombre: "Psicología",
    fecha_hora: "2026-08-12T13:30:00Z",
    estado: "confirmado",
    observaciones: null,
    ...datos,
  };
}

function prepararDatos(turnos: Turno[] = [turno()]) {
  vi.mocked(profesionalService.obtenerMiPerfilProfesional).mockResolvedValue(perfil);
  vi.mocked(disponibilidadService.obtenerDisponibilidadesProfesional).mockResolvedValue([
    { id: 1, profesional_id: 7, dia_semana: 2, hora_inicio: "09:00:00", hora_fin: "13:00:00", activa: true },
  ]);
  vi.mocked(turnoService.obtenerMiAgendaProfesional).mockResolvedValue(turnos);
}

function renderizar() {
  const acciones = {
    agenda: vi.fn(),
    disponibilidad: vi.fn(),
    perfil: vi.fn(),
    salir: vi.fn(),
  };
  render(<DashboardProfesional nombre="Mariana" onAbrirAgenda={acciones.agenda} onAbrirDisponibilidad={acciones.disponibilidad} onAbrirPerfil={acciones.perfil} onCerrarSesion={acciones.salir} />);
  return acciones;
}

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.setSystemTime(new Date("2026-08-12T12:00:00Z"));
  vi.clearAllMocks();
});

afterEach(() => vi.useRealTimers());

describe("dashboard profesional", () => {
  it("renderiza navegación, jornada y disponibilidad con datos propios", async () => {
    prepararDatos();
    renderizar();
    expect(await screen.findByRole("heading", { name: /Buen día, Mariana/ })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Navegación profesional" })).toBeInTheDocument();
    expect(await screen.findByText(/Hoy atendés de 09:00 a 13:00/)).toBeInTheDocument();
    expect(profesionalService.obtenerMiPerfilProfesional).toHaveBeenCalledOnce();
    expect(turnoService.obtenerMiAgendaProfesional).toHaveBeenCalledOnce();
  });

  it("muestra agenda cargada y destaca el próximo turno real", async () => {
    prepararDatos([turno(), turno({ id: 2, paciente_nombre: "Carlos Ruiz", fecha_hora: "2026-08-12T15:00:00Z", estado: "reservado" })]);
    renderizar();
    const agenda = await screen.findByRole("region", { name: "Agenda de hoy" });
    expect(within(agenda).getByText("Lucía Fernández")).toBeInTheDocument();
    expect(within(agenda).getByText("Carlos Ruiz")).toBeInTheDocument();
    expect(screen.getByText("Tenés 2 turnos programados para hoy.")).toBeInTheDocument();
    expect(screen.getAllByText("Lucía Fernández").length).toBeGreaterThan(1);
  });

  it("muestra un estado vacío cuando no hay turnos", async () => {
    prepararDatos([]);
    renderizar();
    expect(await screen.findByRole("heading", { name: "Tu agenda está libre hoy" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "No hay más turnos próximos" })).toBeInTheDocument();
  });

  it("aísla el error de agenda y permite reintentar", async () => {
    prepararDatos([]);
    vi.mocked(turnoService.obtenerMiAgendaProfesional).mockRejectedValueOnce(new Error("red"));
    renderizar();
    expect(await screen.findByRole("alert")).toHaveTextContent("No pudimos cargar tu agenda");
    vi.mocked(turnoService.obtenerMiAgendaProfesional).mockResolvedValueOnce([]);
    fireEvent.click(screen.getByRole("button", { name: /Reintentar/ }));
    await waitFor(() => expect(turnoService.obtenerMiAgendaProfesional).toHaveBeenCalledTimes(2));
  });

  it("conecta la navegación profesional de escritorio y móvil", async () => {
    prepararDatos([]);
    const acciones = renderizar();
    await screen.findByRole("heading", { name: "Tu agenda está libre hoy" });
    fireEvent.click(screen.getAllByRole("button", { name: "Mi agenda" })[0]);
    fireEvent.click(screen.getAllByRole("button", { name: "Mi disponibilidad" })[0]);
    fireEvent.click(screen.getAllByRole("button", { name: "Mi perfil" })[0]);
    expect(acciones.agenda).toHaveBeenCalled();
    expect(acciones.disponibilidad).toHaveBeenCalled();
    expect(acciones.perfil).toHaveBeenCalled();
    expect(screen.getByRole("navigation", { name: "Navegación principal" })).toBeInTheDocument();
  });

  it("mantiene las acciones permitidas para el profesional", async () => {
    prepararDatos();
    vi.mocked(turnoService.finalizarMiTurno).mockResolvedValue(turno({ estado: "finalizado" }));
    renderizar();
    const agenda = await screen.findByRole("region", { name: "Agenda de hoy" });
    fireEvent.click(within(agenda).getByRole("button", { name: /Finalizar/ }));
    await waitFor(() => expect(turnoService.finalizarMiTurno).toHaveBeenCalledWith(1));
    expect(within(agenda).getByText("Finalizado")).toBeInTheDocument();
    expect(within(agenda).queryByRole("button", { name: /Marcar ausente/ })).not.toBeInTheDocument();
  });
});
