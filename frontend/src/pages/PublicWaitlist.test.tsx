import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PublicBooking from "./PublicBooking";
import * as booking from "../services/publicBookingService";
import * as waitlist from "../services/publicWaitlistService";

vi.mock("../services/publicBookingService");
vi.mock("../services/publicWaitlistService");

describe("alta pública de lista de espera", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(booking.obtenerPerfilPublico).mockResolvedValue({ nombre: "Laura", apellido: "Gómez", especialidades: [] });
    vi.mocked(booking.obtenerPrestacionesPublicas).mockResolvedValue([{ identificador_publico: "pub-1", nombre: "Consulta", descripcion: null, duracion_minutos: 30, modalidad: "presencial" }]);
    vi.mocked(booking.obtenerDisponibilidadPublica).mockResolvedValue({ zona_horaria: "America/Argentina/Buenos_Aires", dias: [{ fecha: "2026-09-15", horarios: [] }] });
    vi.mocked(waitlist.crearWaitlistPublica).mockResolvedValue({ message: "ok" });
  });

  it("muestra el CTA cuando no hay horarios y confirma el alta sin exponer IDs", async () => {
    render(<PublicBooking slug="laura" />);
    fireEvent.change(await screen.findByLabelText("Prestación"), { target: { value: "pub-1" } });
    fireEvent.change(screen.getByLabelText("Fecha"), { target: { value: "2026-09-15" } });
    expect(await screen.findByText("No hay horarios disponibles para este día.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Sumarme a la lista de espera" }));
    fireEvent.change(screen.getByLabelText("Nombre"), { target: { value: "Ana" } });
    fireEvent.change(screen.getByLabelText("Apellido"), { target: { value: "Pérez" } });
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "ana@example.com" } });
    fireEvent.click(screen.getByRole("button", { name: "Confirmar lista de espera" }));
    await waitFor(() => expect(waitlist.crearWaitlistPublica).toHaveBeenCalledWith("laura", expect.objectContaining({ prestacion: "pub-1", fecha_desde: "2026-09-15", fecha_hasta: "2026-09-15" })));
    expect(await screen.findByText("Quedaste en la lista de espera")).toBeInTheDocument();
  });
});
