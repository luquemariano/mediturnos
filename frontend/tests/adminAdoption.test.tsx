import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AdopcionAdmin from "../src/components/AdopcionAdmin";
import * as servicio from "../src/services/adminAdoptionService";
import type { AdminAdoptionItem } from "../src/types/adminAdoption";

vi.mock("../src/services/adminAdoptionService", () => ({ obtenerAdopcionAdmin: vi.fn() }));

const item = (overrides: Partial<AdminAdoptionItem> = {}): AdminAdoptionItem => ({
  usuario_id: 1, profesional_id: 2, cuenta_id: 3, nombre: "Ana", apellido: "Pérez", email: "ana@example.com",
  first_login_at: null, last_login_at: null, login_count: 0, last_activity_at: null, days_since_last_activity: null, active_days: 0,
  patients_created: 0, appointments_created: 0, services_created: 0, availabilities_created: 0, clinical_evolutions_created: 0,
  adoption_status: "sin_uso", ...overrides,
});

beforeEach(() => { vi.clearAllMocks(); vi.mocked(servicio.obtenerAdopcionAdmin).mockResolvedValue([item(), item({ profesional_id: 4, nombre: "Bruno", apellido: "López", email: "bruno@example.com", adoption_status: "activo", last_activity_at: "2026-09-10T12:00:00Z", last_login_at: "2026-09-10T11:00:00Z", login_count: 4, patients_created: 3, appointments_created: 2 })]); });

describe("panel de adopción", () => {
  it("muestra cards, tabla, estados y Nunca para fechas vacías", async () => {
    render(<AdopcionAdmin onVolver={vi.fn()} />);
    expect(await screen.findByText("Ana Pérez")).toBeInTheDocument();
    expect(screen.getByText("Bruno López")).toBeInTheDocument();
    expect(screen.getAllByText("Sin uso").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Activo").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Nunca").length).toBeGreaterThan(0);
    expect(screen.getByText("Adopción")).toBeInTheDocument();
  });

  it("envía búsqueda y filtro de estado", async () => {
    render(<AdopcionAdmin onVolver={vi.fn()} />);
    await screen.findByText("Ana Pérez");
    fireEvent.change(screen.getByLabelText("Buscar"), { target: { value: "ana" } });
    fireEvent.change(screen.getByLabelText("Estado"), { target: { value: "activo" } });
    await waitFor(() => expect(servicio.obtenerAdopcionAdmin).toHaveBeenLastCalledWith({ status: "activo", q: "ana" }, expect.any(AbortSignal)), { timeout: 1000 });
  });

  it("muestra detalle, vacío y error", async () => {
    const { unmount } = render(<AdopcionAdmin onVolver={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Ana Pérez" }));
    expect(await screen.findByRole("dialog")).toHaveTextContent("Días activos");
    fireEvent.click(screen.getByRole("button", { name: "Cerrar detalle" }));
    unmount();
    vi.mocked(servicio.obtenerAdopcionAdmin).mockResolvedValueOnce([]);
    const vacio = render(<AdopcionAdmin onVolver={vi.fn()} />);
    expect(await screen.findByRole("heading", { name: "No encontramos profesionales" })).toBeInTheDocument();
    vacio.unmount();
    vi.mocked(servicio.obtenerAdopcionAdmin).mockRejectedValueOnce(new Error("red"));
    render(<AdopcionAdmin onVolver={vi.fn()} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("No pudimos cargar");
  });
});
