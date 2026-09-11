import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SelfService from "./SelfService";
import * as api from "../services/publicBookingService";
import * as analytics from "../analytics";

vi.mock("../services/publicBookingService");
vi.mock("../analytics");

const base = { reserva_id: "r-1", estado: "reservado", fecha_hora: "2026-09-15T10:00:00-03:00", fecha_fin: "2026-09-15T10:30:00-03:00", zona_horaria: "America/Argentina/Buenos_Aires", profesional_slug: "laura-gomez", prestacion_identificador_publico: "p-1", profesional: { nombre: "Laura", apellido: "Gómez" }, prestacion: { nombre: "Consulta", modalidad: "presencial" } };

describe("SelfService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.obtenerReservaPublica).mockResolvedValue(base);
    vi.mocked(api.obtenerDisponibilidadPublica).mockResolvedValue({ zona_horaria: base.zona_horaria, dias: [{ fecha: "2026-09-16", horarios: ["2026-09-16T15:30:00-03:00", "2026-09-16T16:00:00-03:00"] }] });
    vi.mocked(api.cancelarReservaPublica).mockResolvedValue({ ...base, estado: "cancelado" });
    vi.mocked(api.reprogramarReservaPublica).mockResolvedValue({ ...base, fecha_hora: "2026-09-16T15:30:00-03:00" });
  });

  it("consulta slots reales y reprograma usando exactamente el seleccionado", async () => {
    render(<SelfService token="secret" />);
    expect(await screen.findByText("Laura Gómez")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Nueva fecha"), { target: { value: "2026-09-16" } });
    expect(await screen.findByRole("button", { name: /15:30/ })).toBeInTheDocument();
    expect(screen.queryByLabelText("Nueva fecha y hora")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reprogramar" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: /16:00/ }));
    expect(screen.getByRole("button", { name: "Reprogramar" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Reprogramar" }));
    await waitFor(() => expect(api.reprogramarReservaPublica).toHaveBeenCalledWith("secret", "2026-09-16T16:00:00-03:00"));
    expect(await screen.findByText("Tu turno fue reprogramado correctamente.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reprogramar" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Volver a reprogramar" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Volver a reprogramar" }));
    expect(screen.getByLabelText("Nueva fecha")).toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith("public_booking_reschedule", { source: "self_service" });
    expect(localStorage.getItem("secret")).toBeNull();
    expect(sessionStorage.getItem("secret")).toBeNull();
  });

  it("muestra ausencia de disponibilidad y no envía analytics en error", async () => {
    vi.mocked(api.obtenerDisponibilidadPublica).mockResolvedValue({ zona_horaria: base.zona_horaria, dias: [{ fecha: "2026-09-16", horarios: [] }] });
    render(<SelfService token="secret" />);
    fireEvent.change(await screen.findByLabelText("Nueva fecha"), { target: { value: "2026-09-16" } });
    expect(await screen.findByText("No hay horarios disponibles para este día.")).toBeInTheDocument();
    expect(analytics.trackEvent).not.toHaveBeenCalled();
  });

  it("conserva cancelación y sólo envía analytics tras éxito", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<SelfService token="secret" />);
    fireEvent.click(await screen.findByRole("button", { name: "Cancelar turno" }));
    await waitFor(() => expect(api.cancelarReservaPublica).toHaveBeenCalledWith("secret"));
    expect(await screen.findByText("cancelado")).toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith("public_booking_cancel", { source: "self_service" });
  });

  it("reemplaza la pantalla sólo ante error de carga inicial", async () => {
    vi.mocked(api.obtenerReservaPublica).mockRejectedValue(new Error("404"));
    render(<SelfService token="invalid" />);
    expect(await screen.findByText("No encontramos esta reserva.")).toBeInTheDocument();
    expect(screen.queryByText("Tu reserva")).not.toBeInTheDocument();
  });

  it("mantiene la tarjeta ante error de reprogramación y bloquea el slot actual", async () => {
    const error = { isAxiosError: true, response: { status: 409 } };
    vi.mocked(api.reprogramarReservaPublica).mockRejectedValue(error);
    vi.mocked(api.obtenerDisponibilidadPublica).mockResolvedValue({ zona_horaria: base.zona_horaria, dias: [{ fecha: "2026-09-16", horarios: [base.fecha_hora, "2026-09-16T16:00:00-03:00"] }] });
    render(<SelfService token="secret" />);
    fireEvent.change(await screen.findByLabelText("Nueva fecha"), { target: { value: "2026-09-16" } });
    const slotActual = await screen.findByRole("button", { name: /10:00/ });
    expect(slotActual).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: /16:00/ }));
    fireEvent.click(screen.getByRole("button", { name: "Reprogramar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("El horario seleccionado ya no está disponible.");
    expect(screen.getByText("Tu reserva")).toBeInTheDocument();
    expect(analytics.trackEvent).not.toHaveBeenCalledWith("public_booking_reschedule", expect.anything());
  });
});
