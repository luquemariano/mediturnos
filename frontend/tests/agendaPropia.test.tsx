import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import AgendaPropia from "../src/components/AgendaPropia";
import * as pacienteService from "../src/services/pacienteService";
import * as prestacionService from "../src/services/prestacionService";
import * as profesionalService from "../src/services/profesionalService";
import * as servicio from "../src/services/turnoService";
import type { Turno } from "../src/types/turno";
import { diasGrillaMes, finSemana, inicioSemana } from "../src/utils/calendario";

vi.mock("../src/services/turnoService", () => ({
  obtenerMiAgendaProfesional: vi.fn(),
  obtenerMisTurnosPaciente: vi.fn(),
  cancelarMiTurno: vi.fn(),
  cancelarMiTurnoProfesional: vi.fn(),
  finalizarMiTurno: vi.fn(),
  marcarAusenteMiTurno: vi.fn(),
  crearMiTurnoProfesional: vi.fn(),
  obtenerHorariosLibres: vi.fn(),
  reprogramarMiTurnoProfesional: vi.fn(),
}));
vi.mock("../src/services/pacienteService", () => ({ obtenerPacientesParaProfesional: vi.fn() }));
vi.mock("../src/services/prestacionService", () => ({ obtenerMisPrestaciones: vi.fn(), obtenerPrestaciones: vi.fn() }));
vi.mock("../src/services/profesionalService", () => ({ obtenerMiPerfilProfesional: vi.fn() }));
vi.mock("../src/services/disponibilidadService", () => ({ obtenerMisExcepciones: vi.fn().mockResolvedValue([]) }));

function turno(datos: Partial<Turno> = {}): Turno {
  return {
    id: 1,
    paciente_id: 10,
    paciente_nombre: "Ana López",
    prestacion_id: 20,
    prestacion_nombre: "Consulta clínica",
    profesional_nombre: "Sofía Ramírez",
    especialidad_nombre: "Clínica médica",
    fecha_hora: "2026-08-13T12:00:00Z",
    fecha_fin: "2026-08-13T12:50:00Z",
    estado: "confirmado",
    observaciones: "Control de seguimiento.",
    ...datos,
  };
}

const agenda = [
  turno({ id: 3, paciente_nombre: "Carla Sur", fecha_hora: "2026-08-14T17:00:00Z", fecha_fin: "2026-08-14T17:50:00Z", estado: "reservado" }),
  turno({ id: 2, paciente_nombre: "Bruno Paz", fecha_hora: "2026-08-13T11:00:00Z", fecha_fin: "2026-08-13T11:50:00Z", estado: "finalizado" }),
  turno(),
  turno({ id: 4, paciente_nombre: "Diego Sol", fecha_hora: "2026-08-14T18:00:00Z", estado: "ausente", fecha_fin: undefined }),
  turno({ id: 5, paciente_nombre: "Eva Mar", fecha_hora: "2026-08-14T19:00:00Z", estado: "cancelado" }),
];

const acciones = {
  volver: vi.fn(),
  disponibilidad: vi.fn(),
  perfil: vi.fn(),
  salir: vi.fn(),
};

function renderProfesional() {
  return render(<AgendaPropia
    tipo="profesional"
    nombre="Sofía Ramírez"
    onVolver={acciones.volver}
    onAbrirDisponibilidad={acciones.disponibilidad}
    onAbrirPerfil={acciones.perfil}
    onCerrarSesion={acciones.salir}
  />);
}

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  vi.setSystemTime(new Date("2026-08-13T11:30:00Z"));
  vi.clearAllMocks();
});

afterEach(() => vi.useRealTimers());

describe("agenda propia profesional Signature", () => {
  it("inicia en hoy, consulta un rango civil y conserva un día vacío al navegar", async () => {
    vi.setSystemTime(new Date("2026-08-31T12:00:00Z"));
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue([]);
    renderProfesional();
    expect(await screen.findByText(/Lunes, 31 de agosto de 2026/i)).toBeInTheDocument();
    expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledWith({ desde: "2026-08-31", hasta: "2026-08-31" });
    expect(screen.getByRole("button", { name: "Día" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Semana" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Mes" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Fecha siguiente" }));
    expect(await screen.findByText(/Martes, 1 de septiembre de 2026/i)).toBeInTheDocument();
    expect(screen.getByText("No tenés turnos para este día.")).toBeInTheDocument();
    expect(servicio.obtenerMiAgendaProfesional).toHaveBeenLastCalledWith({ desde: "2026-09-01", hasta: "2026-09-01" });
  });

  it("usa el endpoint propio y el shell profesional compartido", async () => {
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue([]);
    renderProfesional();
    await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledOnce());
    expect(servicio.obtenerMisTurnosPaciente).not.toHaveBeenCalled();
    expect(screen.getByRole("navigation", { name: "Navegación profesional" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Mi agenda" })[0]).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("button", { name: "+ Nuevo turno" })).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: "Inicio" })[0]);
    fireEvent.click(screen.getAllByRole("button", { name: "Mi disponibilidad" })[0]);
    fireEvent.click(screen.getAllByRole("button", { name: "Mi perfil" })[0]);
    fireEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));
    expect(acciones.volver).toHaveBeenCalled();
    expect(acciones.disponibilidad).toHaveBeenCalled();
    expect(acciones.perfil).toHaveBeenCalled();
    expect(acciones.salir).toHaveBeenCalled();
  });

  it("agrupa por fecha local, marca Hoy y ordena cronológicamente", async () => {
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue(agenda);
    renderProfesional();
    const hoy = await screen.findByRole("heading", { name: /Jueves, 13 de agosto de 2026/i });
    expect(hoy).toBeInTheDocument();
    const filas = screen.getAllByRole("article");
    expect(filas[0]).toHaveAccessibleName(/08:00–08:50, Bruno Paz/);
    expect(filas[1]).toHaveAccessibleName(/09:00–09:50, Ana López/);
    expect(screen.getByText("09:00–09:50")).toBeInTheDocument();
  });

  it("navega localmente entre fechas sin ocultar los grupos", async () => {
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue(agenda);
    renderProfesional();
    await screen.findByRole("heading", { name: /Jueves, 13 de agosto de 2026/i });
    fireEvent.click(screen.getByRole("button", { name: "Fecha siguiente" }));
    expect(screen.getByRole("navigation", { name: "Navegación temporal" })).toHaveTextContent("Viernes, 14 de agosto de 2026");
    expect(await screen.findByText("Carla Sur")).toBeInTheDocument();
  });

  it("representa estados sin pills y destaca el próximo turno", async () => {
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue(agenda);
    renderProfesional();
    const ana = await screen.findByLabelText(/Ana López, Confirmado/);
    expect(ana.closest("li")).toHaveClass("es-proximo", "estado-confirmado");
    expect(screen.getByLabelText(/Bruno Paz, Finalizado/).closest("li")).toHaveClass("estado-finalizado");
  });

  it("expande una sola fila activa por toque o teclado", async () => {
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue([
      turno({ id: 1, fecha_hora: "2026-08-13T10:00:00Z" }),
      turno({ id: 2, paciente_nombre: "Bruno", fecha_hora: "2026-08-13T11:00:00Z", estado: "reservado" }),
    ]);
    renderProfesional();
    const primera = await screen.findByLabelText(/Ana López/);
    const segunda = screen.getByLabelText(/Bruno/);
    fireEvent.click(primera);
    expect(primera).toHaveAttribute("aria-expanded", "true");
    fireEvent.keyDown(segunda, { key: " " });
    expect(primera).toHaveAttribute("aria-expanded", "false");
    expect(segunda).toHaveAttribute("aria-expanded", "true");
  });

  it("bloquea las dos acciones del turno durante la petición y actualiza el estado", async () => {
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue([turno()]);
    let resolver!: (valor: Turno) => void;
    vi.mocked(servicio.finalizarMiTurno).mockReturnValue(new Promise((resolve) => { resolver = resolve; }));
    renderProfesional();
    const fila = await screen.findByLabelText(/Ana López/);
    fireEvent.click(within(fila).getByRole("button", { name: "Finalizar" }));
    expect(within(fila).getByRole("button", { name: "Actualizando…" })).toBeDisabled();
    expect(within(fila).getByRole("button", { name: "Marcar ausente" })).toBeDisabled();
    expect(within(fila).getByRole("status")).toHaveTextContent("Actualizando turno");
    resolver(turno({ estado: "finalizado" }));
    await waitFor(() => expect(screen.getByLabelText(/Ana López, Finalizado/)).toBeInTheDocument());
  });

  it("muestra un error de acción asociado sin perder la agenda", async () => {
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue([turno()]);
    vi.mocked(servicio.marcarAusenteMiTurno).mockRejectedValue(new Error("red"));
    renderProfesional();
    const fila = await screen.findByLabelText(/Ana López/);
    fireEvent.click(within(fila).getByRole("button", { name: "Marcar ausente" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("No pudimos actualizar el turno");
    expect(screen.getByText("Ana López")).toBeInTheDocument();
  });

  it("confirma y cancela un turno profesional sin recargar la agenda", async () => {
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue([turno()]);
    vi.mocked(servicio.cancelarMiTurnoProfesional).mockResolvedValue(turno({ estado: "cancelado" }));
    renderProfesional();
    const fila = await screen.findByLabelText(/Ana López/);
    fireEvent.click(within(fila).getByRole("button", { name: "Cancelar" }));
    const dialogo = screen.getByRole("dialog", { name: "Cancelar turno" });
    expect(within(dialogo).getByText("Ana López")).toBeInTheDocument();
    expect(within(dialogo).getByText("Consulta clínica")).toBeInTheDocument();
    fireEvent.click(within(dialogo).getByRole("button", { name: "Cancelar turno" }));
    expect(await screen.findByText("Turno cancelado correctamente.")).toHaveAttribute("role", "status");
    expect(screen.getByLabelText(/Ana López, Cancelado/)).toBeInTheDocument();
    expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledTimes(1);
  });

  it("bloquea doble cancelación y muestra el error dentro de la confirmación", async () => {
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue([turno()]);
    let rechazar!: (motivo: unknown) => void;
    vi.mocked(servicio.cancelarMiTurnoProfesional).mockReturnValue(new Promise((_, reject) => { rechazar = reject; }));
    renderProfesional();
    fireEvent.click(within(await screen.findByLabelText(/Ana López/)).getByRole("button", { name: "Cancelar" }));
    const confirmar = within(screen.getByRole("dialog")).getByRole("button", { name: "Cancelar turno" });
    fireEvent.click(confirmar);
    fireEvent.click(confirmar);
    expect(servicio.cancelarMiTurnoProfesional).toHaveBeenCalledTimes(1);
    expect(within(screen.getByRole("dialog")).getByRole("button", { name: "Cancelando…" })).toBeDisabled();
    rechazar(new Error("red"));
    expect(await within(screen.getByRole("dialog")).findByRole("alert")).toHaveTextContent("No pudimos cancelar el turno");
  });

  it("reprograma usando slots que excluyen el turno actual", async () => {
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue([turno()]);
    vi.mocked(servicio.obtenerHorariosLibres).mockResolvedValue([{ fecha_hora: "2026-08-15T15:00:00Z" }]);
    vi.mocked(servicio.reprogramarMiTurnoProfesional).mockResolvedValue(turno({ fecha_hora: "2026-08-15T15:00:00Z", fecha_fin: "2026-08-15T15:50:00Z" }));
    renderProfesional();
    fireEvent.click(within(await screen.findByLabelText(/Ana López/)).getByRole("button", { name: "Reprogramar" }));
    const dialogo = screen.getByRole("dialog", { name: "Reprogramar turno" });
    fireEvent.change(within(dialogo).getByLabelText("Nueva fecha"), { target: { value: "2026-08-15" } });
    expect(servicio.obtenerHorariosLibres).toHaveBeenCalledWith(20, "2026-08-15", 1);
    fireEvent.click(await within(dialogo).findByRole("radio", { name: "12:00" }));
    fireEvent.click(within(dialogo).getByRole("button", { name: "Confirmar cambio" }));
    expect(await screen.findByText("Turno reprogramado correctamente.")).toHaveAttribute("role", "status");
    expect(servicio.reprogramarMiTurnoProfesional).toHaveBeenCalledWith(1, "2026-08-15T15:00:00Z");
  });

  it("muestra fecha sin slots y conserva un conflicto 409", async () => {
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue([turno()]);
    vi.mocked(servicio.obtenerHorariosLibres).mockResolvedValueOnce([]).mockResolvedValueOnce([{ fecha_hora: "2026-08-15T15:00:00Z" }]).mockResolvedValueOnce([]);
    vi.mocked(servicio.reprogramarMiTurnoProfesional).mockRejectedValue({ isAxiosError: true, response: { status: 409, data: { detail: "El horario ya no está disponible." } } });
    renderProfesional();
    fireEvent.click(within(await screen.findByLabelText(/Ana López/)).getByRole("button", { name: "Reprogramar" }));
    const dialogo = screen.getByRole("dialog");
    fireEvent.change(within(dialogo).getByLabelText("Nueva fecha"), { target: { value: "2026-08-14" } });
    expect(await within(dialogo).findByText("No hay horarios disponibles para esta fecha.")).toBeInTheDocument();
    fireEvent.change(within(dialogo).getByLabelText("Nueva fecha"), { target: { value: "2026-08-15" } });
    fireEvent.click(await within(dialogo).findByRole("radio", { name: "12:00" }));
    fireEvent.click(within(dialogo).getByRole("button", { name: "Confirmar cambio" }));
    expect(await within(dialogo).findByRole("alert")).toHaveTextContent("El horario ya no está disponible");
  });

  it("incorpora el turno creado y muestra feedback sin recargar la agenda", async () => {
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue([]);
    vi.mocked(pacienteService.obtenerPacientesParaProfesional).mockResolvedValue([{ id: 10, nombre: "Ana", apellido: "López" }]);
    vi.mocked(profesionalService.obtenerMiPerfilProfesional).mockResolvedValue({ id: 7, nombre: "Sofía", apellido: "Ramírez", matricula: "MP", telefono: null, email: null, activo: true, especialidades: [] });
    vi.mocked(prestacionService.obtenerMisPrestaciones).mockResolvedValue([{ id: 20, nombre: "Consulta clínica", descripcion: null, duracion_minutos: 50, precio: 100, modalidad: "presencial", activa: true, profesional_id: 7, especialidad_id: 1 }]);
    vi.mocked(servicio.obtenerHorariosLibres).mockResolvedValue([{ fecha_hora: "2026-08-14T12:00:00Z" }]);
    vi.mocked(servicio.crearMiTurnoProfesional).mockResolvedValue(turno({ id: 8, fecha_hora: "2026-08-13T12:00:00Z" }));
    renderProfesional();
    fireEvent.click(await screen.findByRole("button", { name: "+ Nuevo turno" }));
    await screen.findByRole("option", { name: "López, Ana" });
    fireEvent.change(screen.getByLabelText("Paciente"), { target: { value: "10" } });
    fireEvent.change(screen.getByLabelText("Prestación"), { target: { value: "20" } });
    fireEvent.change(screen.getByLabelText("Fecha"), { target: { value: "2026-08-13" } });
    fireEvent.click(await screen.findByRole("radio", { name: "09:00" }));
    fireEvent.click(screen.getByRole("button", { name: "Confirmar turno" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Turno creado correctamente");
    expect(screen.getByText("Ana López")).toBeInTheDocument();
    expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledTimes(1);
  });

  it("representa loading, error con retry y empty state", async () => {
    let rechazar!: (motivo: unknown) => void;
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockReturnValueOnce(new Promise((_, reject) => { rechazar = reject; }));
    const vista = renderProfesional();
    expect(screen.getByLabelText("Cargando agenda")).toBeInTheDocument();
    rechazar(new Error("red"));
    expect(await screen.findByRole("alert")).toHaveTextContent("No pudimos cargar tu agenda");
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValueOnce([]);
    fireEvent.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByRole("heading", { name: "No tenés turnos para este día." })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Fecha anterior" })).toBeInTheDocument();
    vista.unmount();
  });

  it("mantiene Mes ante error y reintenta exactamente el mismo rango visual", async () => {
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValueOnce([]).mockRejectedValueOnce(new Error("red")).mockResolvedValueOnce([]);
    renderProfesional();
    await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledOnce());
    fireEvent.click(screen.getByRole("button", { name: "Mes" }));
    const rango = { desde: diasGrillaMes("2026-08-13")[0], hasta: diasGrillaMes("2026-08-13").at(-1)! };
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mes" })).toHaveAttribute("aria-pressed", "true");
    expect(servicio.obtenerMiAgendaProfesional).toHaveBeenLastCalledWith(rango);
    fireEvent.click(screen.getByRole("button", { name: "Reintentar" }));
    await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledTimes(3));
    expect(servicio.obtenerMiAgendaProfesional).toHaveBeenLastCalledWith(rango);
  });

  it("mantiene toolbar y navegación durante loading mensual", async () => {
    let resolver!: (valor: Turno[]) => void;
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValueOnce([]).mockReturnValueOnce(new Promise((resolve) => { resolver = resolve; }));
    renderProfesional();
    await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledOnce());
    fireEvent.click(screen.getByRole("button", { name: "Mes" }));
    expect(screen.getByRole("button", { name: "Mes" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("navigation", { name: "Navegación temporal" })).toBeInTheDocument();
    expect(await screen.findByRole("status")).toHaveTextContent("Cargando mes");
    resolver([]);
    expect(await screen.findByRole("grid", { name: /Calendario/ })).toBeInTheDocument();
  });

  it("cambia Mes y Semana conservando la fecha de referencia", async () => {
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue([]);
    renderProfesional();
    await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledOnce());
    fireEvent.click(screen.getByRole("button", { name: "Mes" }));
    await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledTimes(2));
    fireEvent.click(screen.getByRole("button", { name: "Semana" }));
    await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledTimes(3));
    expect(servicio.obtenerMiAgendaProfesional).toHaveBeenLastCalledWith({ desde: inicioSemana("2026-08-13"), hasta: finSemana("2026-08-13") });
    expect(screen.getByRole("button", { name: "Semana" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: "Mes" }));
    await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledTimes(4));
    expect(servicio.obtenerMiAgendaProfesional).toHaveBeenLastCalledWith({ desde: diasGrillaMes("2026-08-13")[0], hasta: diasGrillaMes("2026-08-13").at(-1)! });
  });
});

it("conserva la variante paciente y su endpoint propio", async () => {
  vi.useRealTimers();
  vi.mocked(servicio.obtenerMisTurnosPaciente).mockResolvedValue([turno()]);
  render(<AgendaPropia tipo="paciente" onVolver={vi.fn()} />);
  await waitFor(() => expect(servicio.obtenerMisTurnosPaciente).toHaveBeenCalledOnce());
  expect(servicio.obtenerMiAgendaProfesional).not.toHaveBeenCalled();
  expect(screen.getByRole("heading", { name: "Mis turnos" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Cancelar turno" })).toBeInTheDocument();
  expect(screen.queryByRole("navigation", { name: "Navegación profesional" })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "+ Nuevo turno" })).not.toBeInTheDocument();
});
