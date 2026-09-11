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
    expect(await screen.findByRole("button", { name: /03:30/ })).toBeInTheDocument();
    expect(screen.queryByLabelText("Nueva fecha y hora")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reprogramar" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: /04:00/ }));
    expect(screen.getByRole("button", { name: "Reprogramar" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "Reprogramar" }));
    await waitFor(() => expect(api.reprogramarReservaPublica).toHaveBeenCalledWith("secret", "2026-09-16T16:00:00-03:00"));
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
});
