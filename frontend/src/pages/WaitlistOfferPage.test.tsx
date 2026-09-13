import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { beforeEach, describe, expect, it, vi } from "vitest";
import WaitlistOfferPage from "./WaitlistOfferPage";
import * as service from "../services/publicWaitlistService";

vi.mock("../services/publicWaitlistService");

const oferta = { estado: "activa" as const, profesional: "Laura Gómez", prestacion: "Consulta", fecha_hora: "2026-09-15T10:00:00-03:00", expires_at: "2026-09-15T10:30:00-03:00", paciente: "Ana Pérez" };

describe("oferta pública de lista de espera", () => {
  beforeEach(() => { vi.clearAllMocks(); vi.mocked(service.obtenerOfertaWaitlist).mockResolvedValue(oferta); vi.mocked(service.aceptarOfertaWaitlist).mockResolvedValue({ ...oferta, estado: "aceptada" }); });
  it("muestra sólo datos públicos y acepta una oferta una sola vez desde la UI", async () => {
    render(<WaitlistOfferPage token="secret-token" />);
    expect(await screen.findByText("Encontramos un horario para vos")).toBeInTheDocument();
    expect(screen.queryByText("secret-token")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Aceptar horario" }));
    await waitFor(() => expect(service.aceptarOfertaWaitlist).toHaveBeenCalledWith("secret-token"));
    expect(await screen.findByText("Tu turno quedó reservado")).toBeInTheDocument();
  });
});
