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
  nombre: "Sofía",
  apellido: "Ramírez",
  matricula: "MP-DEMO-PSIQ-001",
  telefono: null,
  email: "sofia@example.com",
  activo: true,
  especialidades: [],
};

function turno(datos: Partial<Turno> = {}): Turno {
  return {
    id: 1,
    paciente_id: 4,
    paciente_nombre: "Juan Pérez",
    prestacion_id: 5,
    prestacion_nombre: "Consulta psiquiátrica",
    profesional_nombre: "Sofía Ramírez",
    especialidad_nombre: "Psiquiatría",
    fecha_hora: "2026-08-12T11:00:00Z",
    fecha_fin: "2026-08-12T11:50:00Z",
    estado: "finalizado",
    observaciones: null,
    ...datos,
  };
}

const jornada: Turno[] = [
  turno(),
  turno({ id: 2, paciente_nombre: "Silvina Pérez", fecha_hora: "2026-08-12T12:00:00Z", fecha_fin: "2026-08-12T12:50:00Z", estado: "confirmado" }),
  turno({ id: 3, paciente_nombre: "Ana López", fecha_hora: "2026-08-12T13:00:00Z", fecha_fin: "2026-08-12T13:50:00Z", estado: "ausente", observaciones: "El paciente no se presentó." }),
  turno({ id: 4, paciente_nombre: "Roberto Sánchez", fecha_hora: "2026-08-12T17:00:00Z", fecha_fin: "2026-08-12T17:50:00Z", estado: "confirmado" }),
  turno({ id: 5, paciente_nombre: "Mariana Torres", fecha_hora: "2026-08-12T18:00:00Z", fecha_fin: "2026-08-12T18:50:00Z", estado: "reservado" }),
  turno({ id: 6, paciente_nombre: "Diego Ferreyra", fecha_hora: "2026-08-12T19:00:00Z", fecha_fin: "2026-08-12T19:50:00Z", estado: "cancelado", observaciones: "Cancelación informada por el paciente." }),
];

function prepararDatos(turnos: Turno[] = jornada) {
  vi.mocked(profesionalService.obtenerMiPerfilProfesional).mockResolvedValue(perfil);
  vi.mocked(disponibilidadService.obtenerDisponibilidadesProfesional).mockResolvedValue([
    { id: 1, profesional_id: 7, dia_semana: 2, hora_inicio: "08:00:00", hora_fin: "12:00:00", activa: true },
    { id: 2, profesional_id: 7, dia_semana: 2, hora_inicio: "14:00:00", hora_fin: "19:00:00", activa: true },
  ]);
  vi.mocked(turnoService.obtenerMiAgendaProfesional).mockResolvedValue(turnos);
}

function renderizar() {
  const acciones = { agenda: vi.fn(), disponibilidad: vi.fn(), perfil: vi.fn(), salir: vi.fn() };
  render(<DashboardProfesional nombre="Sofía" onAbrirAgenda={acciones.agenda} onAbrirDisponibilidad={acciones.disponibilidad} onAbrirPerfil={acciones.perfil} onCerrarSesion={acciones.salir} />);
  return acciones;
}

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.setSystemTime(new Date("2026-08-12T11:30:00Z"));
  vi.clearAllMocks();
});

afterEach(() => vi.useRealTimers());

describe("dashboard profesional Signature", () => {
  it.each([
    ["2026-08-13T11:30:00Z", "Buen día, Sofía"],
    ["2026-08-13T18:20:00Z", "Buenas tardes, Sofía"],
    ["2026-08-14T00:45:00Z", "Buenas noches, Sofía"],
    ["2026-08-13T04:15:00Z", "Buenas noches, Sofía"],
  ])("calcula el saludo local para %s", async (fecha, esperado) => {
    vi.setSystemTime(new Date(fecha));
    prepararDatos([]);
    renderizar();
    expect(await screen.findByRole("heading", { name: esperado })).toBeInTheDocument();
  });

  it("renderiza navegación, saludo y resumen textual de la jornada", async () => {
    prepararDatos();
    renderizar();
    expect(await screen.findByRole("heading", { name: "Buen día, Sofía" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Navegación profesional" })).toBeInTheDocument();
    expect(screen.getByLabelText("Resumen de la jornada")).toHaveTextContent("6 turnos");
    expect(screen.getByLabelText("Resumen de la jornada")).toHaveTextContent("2 confirmados");
    expect(screen.getByLabelText("Resumen de la jornada")).toHaveTextContent("1 pendiente");
    expect(screen.getByLabelText("Resumen de la jornada")).toHaveTextContent("3 resueltos");
  });

  it("divide la agenda real en mañana y tarde", async () => {
    prepararDatos();
    renderizar();
    const agenda = await screen.findByRole("region", { name: "Agenda de hoy" });
    expect(within(agenda).getByRole("heading", { name: "Mañana" })).toBeInTheDocument();
    expect(within(agenda).getByRole("heading", { name: "Tarde" })).toBeInTheDocument();
    expect(within(agenda).getByText("08:00–12:00")).toBeInTheDocument();
    expect(within(agenda).getByText("14:00–19:00")).toBeInTheDocument();
    expect(within(agenda).getByText("Juan Pérez")).toBeInTheDocument();
    expect(within(agenda).getByText("Diego Ferreyra")).toBeInTheDocument();
  });

  it("destaca el próximo turno con datos y rango reales", async () => {
    prepararDatos();
    renderizar();
    const proximo = await screen.findByRole("region", { name: "Silvina Pérez" });
    expect(within(proximo).getByText("09:00")).toBeInTheDocument();
    expect(within(proximo).getByText("Consulta psiquiátrica")).toBeInTheDocument();
    expect(within(proximo).getByText("09:00–09:50")).toBeInTheDocument();
    expect(within(proximo).getByText("Confirmado")).toBeInTheDocument();
    const sectorEstado = within(proximo).getByText("Confirmado").closest(".prof-proximo-estado");
    expect(sectorEstado).toHaveClass("estado-confirmado");
    expect(within(proximo).getByRole("button", { name: "Ir a la agenda" })).toBeInTheDocument();
  });

  it("muestra estados terminales sin acciones", async () => {
    prepararDatos();
    renderizar();
    const agenda = await screen.findByRole("region", { name: "Agenda de hoy" });
    for (const nombre of ["Juan Pérez", "Ana López", "Diego Ferreyra"]) {
      const fila = within(agenda).getByLabelText(new RegExp(nombre));
      expect(within(fila).queryByRole("button", { name: "Finalizar" })).not.toBeInTheDocument();
      expect(within(fila).queryByRole("button", { name: "Marcar ausente" })).not.toBeInTheDocument();
    }
    expect(within(agenda).getByLabelText(/Juan Pérez, Finalizado/)).toBeInTheDocument();
    expect(within(agenda).getByText("Ausente")).toBeInTheDocument();
    expect(within(agenda).getByText("Cancelado")).toBeInTheDocument();
  });

  it("expande una sola fila activa por toque o teclado", async () => {
    prepararDatos();
    renderizar();
    const agenda = await screen.findByRole("region", { name: "Agenda de hoy" });
    const roberto = within(agenda).getByLabelText(/Roberto Sánchez/);
    const mariana = within(agenda).getByLabelText(/Mariana Torres/);
    expect(roberto).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(roberto);
    expect(roberto).toHaveAttribute("aria-expanded", "true");
    fireEvent.keyDown(mariana, { key: "Enter" });
    expect(roberto).toHaveAttribute("aria-expanded", "false");
    expect(mariana).toHaveAttribute("aria-expanded", "true");
  });

  it("mantiene las acciones permitidas para el próximo turno", async () => {
    prepararDatos();
    vi.mocked(turnoService.finalizarMiTurno).mockResolvedValue({ ...jornada[1], estado: "finalizado" });
    renderizar();
    const agenda = await screen.findByRole("region", { name: "Agenda de hoy" });
    const fila = within(agenda).getByLabelText(/Silvina Pérez/);
    fireEvent.click(within(fila).getByRole("button", { name: /Finalizar/ }));
    await waitFor(() => expect(turnoService.finalizarMiTurno).toHaveBeenCalledWith(2));
    expect(within(agenda).getByLabelText(/Silvina Pérez, Finalizado/)).toBeInTheDocument();
  });

  it("muestra el indicador Ahora sólo dentro de disponibilidad", async () => {
    prepararDatos();
    const { unmount } = renderizarConResultado();
    expect(await screen.findByRole("status")).toHaveTextContent("Ahora");
    unmount();

    vi.setSystemTime(new Date("2026-08-12T01:00:00Z"));
    prepararDatos();
    renderizar();
    await screen.findByRole("heading", { name: "Agenda de hoy" });
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("conserva estado vacío y navegación móvil estructural", async () => {
    prepararDatos([]);
    const acciones = renderizar();
    expect(await screen.findByRole("heading", { name: "Tu agenda está libre hoy" })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Navegación principal" })).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: "Mi agenda" })[0]);
    expect(acciones.agenda).toHaveBeenCalled();
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
});

function renderizarConResultado() {
  const acciones = { agenda: vi.fn(), disponibilidad: vi.fn(), perfil: vi.fn(), salir: vi.fn() };
  return render(<DashboardProfesional nombre="Sofía" onAbrirAgenda={acciones.agenda} onAbrirDisponibilidad={acciones.disponibilidad} onAbrirPerfil={acciones.perfil} onCerrarSesion={acciones.salir} />);
}
