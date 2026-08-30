import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import AgendaPropia from "../src/components/AgendaPropia";
import * as servicio from "../src/services/turnoService";
import { diasGrillaMes, finSemana, inicioSemana } from "../src/utils/calendario";
import * as disponibilidad from "../src/services/disponibilidadService";

vi.mock("../src/services/turnoService", () => ({ obtenerMiAgendaProfesional: vi.fn(), obtenerMisTurnosPaciente: vi.fn(), cancelarMiTurno: vi.fn(), cancelarMiTurnoProfesional: vi.fn(), finalizarMiTurno: vi.fn(), marcarAusenteMiTurno: vi.fn(), crearMiTurnoProfesional: vi.fn(), obtenerHorariosLibres: vi.fn(), reprogramarMiTurnoProfesional: vi.fn() }));
vi.mock("../src/services/disponibilidadService", () => ({ obtenerMisExcepciones: vi.fn() }));

const props = { tipo: "profesional" as const, onVolver: vi.fn() };
const turno = { id: 1, paciente_id: 1, paciente_nombre: "Ana López", prestacion_id: 1, prestacion_nombre: "Consulta clínica", profesional_nombre: "Profesional", especialidad_nombre: "Clínica", fecha_hora: "2026-08-13T15:00:00Z", fecha_fin: "2026-08-13T15:30:00Z", estado: "confirmado" as const, observaciones: null };
function renderAgenda() { return render(<AgendaPropia {...props} />); }

beforeEach(() => { vi.useFakeTimers({ shouldAdvanceTime: true }); vi.setSystemTime(new Date("2026-08-13T11:30:00Z")); vi.clearAllMocks(); vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue([]); vi.mocked(disponibilidad.obtenerMisExcepciones).mockResolvedValue([]); });
afterEach(() => vi.useRealTimers());

describe("integración F10.6 de agenda profesional", () => {
  it("mantiene Hoy deshabilitado en Día, Semana y Mes actuales", async () => {
    renderAgenda(); await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledOnce());
    expect(screen.getByRole("button", { name: "Hoy" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Semana" })); await waitFor(() => expect(screen.getByRole("button", { name: "Semana" })).toHaveAttribute("aria-pressed", "true"));
    expect(screen.getByRole("button", { name: "Hoy" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Mes" })); await waitFor(() => expect(screen.getByRole("button", { name: "Mes" })).toHaveAttribute("aria-pressed", "true"));
    expect(screen.getByRole("button", { name: "Hoy" })).toBeDisabled();
  });

  it("carga excepciones por rango sin romper la agenda si falla", async () => {
    vi.mocked(disponibilidad.obtenerMisExcepciones).mockRejectedValue(new Error("red"));
    renderAgenda(); await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledOnce()); await waitFor(() => expect(disponibilidad.obtenerMisExcepciones).toHaveBeenCalledOnce());
    fireEvent.click(screen.getByRole("button", { name: "Semana" })); await waitFor(() => expect(screen.getByRole("button", { name: "Semana" })).toHaveAttribute("aria-pressed", "true"));
    fireEvent.click(screen.getByRole("button", { name: "Mes" })); await waitFor(() => expect(screen.getByRole("button", { name: "Mes" })).toHaveAttribute("aria-pressed", "true"));
    expect(disponibilidad.obtenerMisExcepciones).toHaveBeenCalledTimes(3);
    expect(disponibilidad.obtenerMisExcepciones).toHaveBeenNthCalledWith(1, { desde: "2026-08-13", hasta: "2026-08-13" });
    expect(disponibilidad.obtenerMisExcepciones).toHaveBeenNthCalledWith(2, { desde: "2026-08-10", hasta: "2026-08-16" });
    expect(disponibilidad.obtenerMisExcepciones).toHaveBeenNthCalledWith(3, { desde: diasGrillaMes("2026-08-13")[0], hasta: diasGrillaMes("2026-08-13").at(-1)! });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument(); expect(screen.getByRole("grid")).toBeInTheDocument();
  });

  it("habilita Hoy en períodos no actuales y vuelve con una sola carga", async () => {
    renderAgenda(); await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledOnce());
    fireEvent.click(screen.getByRole("button", { name: "Semana" })); await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledTimes(2));
    fireEvent.click(screen.getByRole("button", { name: "Fecha anterior" })); await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledTimes(3));
    expect(screen.getByRole("button", { name: "Hoy" })).toBeEnabled(); fireEvent.click(screen.getByRole("button", { name: "Hoy" }));
    await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledTimes(4));
    expect(servicio.obtenerMiAgendaProfesional).toHaveBeenLastCalledWith({ desde: inicioSemana("2026-08-13"), hasta: finSemana("2026-08-13") }); expect(screen.getByRole("button", { name: "Hoy" })).toBeDisabled();
  });

  it("preserva la fecha de referencia y consulta una vez por transición", async () => {
    renderAgenda(); await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledOnce());
    fireEvent.click(screen.getByRole("button", { name: "Semana" })); await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledTimes(2));
    fireEvent.click(screen.getByRole("button", { name: "Mes" })); await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledTimes(3));
    fireEvent.click(screen.getByRole("button", { name: "Semana" })); await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledTimes(4));
    expect(servicio.obtenerMiAgendaProfesional).toHaveBeenLastCalledWith({ desde: inicioSemana("2026-08-13"), hasta: finSemana("2026-08-13") });
  });

  it("carga Mes → Día mediante una sola consulta diaria", async () => {
    renderAgenda(); await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledOnce()); fireEvent.click(screen.getByRole("button", { name: "Mes" })); await waitFor(() => expect(screen.getByRole("grid")).toBeInTheDocument());
    const antes = servicio.obtenerMiAgendaProfesional.mock.calls.length; fireEvent.click(screen.getByRole("button", { name: /jueves, 13 de agosto/i }));
    await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledTimes(antes + 1)); expect(servicio.obtenerMiAgendaProfesional).toHaveBeenLastCalledWith({ desde: "2026-08-13", hasta: "2026-08-13" }); expect(screen.getByRole("button", { name: "Día" })).toHaveAttribute("aria-pressed", "true");
  });

  it.each([["dia", { desde: "2026-08-13", hasta: "2026-08-13" }], ["semana", { desde: "2026-08-10", hasta: "2026-08-16" }], ["mes", { desde: diasGrillaMes("2026-08-13")[0], hasta: diasGrillaMes("2026-08-13").at(-1)! }]])("permite retry sin cambiar vista en %s", async (vista, rango) => {
    if (vista === "dia") vi.mocked(servicio.obtenerMiAgendaProfesional).mockReset().mockRejectedValueOnce(new Error("red")).mockResolvedValueOnce([]);
    else vi.mocked(servicio.obtenerMiAgendaProfesional).mockReset().mockResolvedValueOnce([]).mockRejectedValueOnce(new Error("red")).mockResolvedValueOnce([]);
    renderAgenda(); await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledOnce());
    if (vista !== "dia") { fireEvent.click(screen.getByRole("button", { name: vista === "semana" ? "Semana" : "Mes" })); await screen.findByRole("alert"); }
    else await screen.findByRole("alert");
    expect(screen.getByRole("button", { name: vista === "dia" ? "Día" : vista === "semana" ? "Semana" : "Mes" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: "Reintentar" })); await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenLastCalledWith(rango));
  });

  it("mantiene controles accesibles y estructura móvil lógica", async () => {
    renderAgenda(); await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledOnce()); fireEvent.click(screen.getByRole("button", { name: "Semana" })); await screen.findByRole("group", { name: "Días de la semana" });
    expect(screen.getAllByRole("button", { name: /^(lun|mar|mié|jue|vie|sáb|dom)/i })).toHaveLength(7); expect(screen.getAllByRole("button").some((boton) => boton.tabIndex > 0)).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Mes" })); await screen.findByRole("grid"); expect(screen.getAllByRole("button").filter((boton) => boton.className.includes("agenda-mes-celda"))).toHaveLength(42);
  });

  it("transiciona de detalle a reprogramación sin cerrar el modal", async () => {
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue([turno]); renderAgenda(); await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledOnce());
    fireEvent.click(screen.getByRole("button", { name: "Semana" })); const bloque = await screen.findByRole("button", { name: /12:00, Ana López, Consulta clínica, confirmado/i }); fireEvent.click(bloque); const dialogo = await screen.findByRole("dialog", { name: "Detalle del turno" }); expect(screen.getByText("Confirmado")).toBeInTheDocument(); expect(screen.queryByText("Nueva fecha")).not.toBeInTheDocument(); fireEvent.click(within(dialogo).getByRole("button", { name: "Reprogramar" })); expect(await screen.findByRole("dialog", { name: "Reprogramar turno" })).toBe(dialogo); expect(screen.getByLabelText("Nueva fecha")).toBeInTheDocument(); expect(screen.getByRole("group", { name: "Nuevo horario" })).toBeInTheDocument();
  });

  it("transiciona de detalle a cancelación y conserva la advertencia", async () => {
    vi.mocked(servicio.obtenerMiAgendaProfesional).mockResolvedValue([turno]); renderAgenda(); await waitFor(() => expect(servicio.obtenerMiAgendaProfesional).toHaveBeenCalledOnce()); fireEvent.click(screen.getByRole("button", { name: "Semana" })); const bloque = await screen.findByRole("button", { name: /12:00, Ana López, Consulta clínica, confirmado/i }); fireEvent.click(bloque); const dialogo = await screen.findByRole("dialog", { name: "Detalle del turno" }); fireEvent.click(within(dialogo).getByRole("button", { name: "Cancelar" })); expect(await screen.findByRole("dialog", { name: "Cancelar turno" })).toBe(dialogo); expect(screen.getByText(/El turno quedará cancelado/)).toBeInTheDocument(); expect(screen.queryByLabelText("Nueva fecha")).not.toBeInTheDocument();
  });
});
