import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ConsultorioInvitationPage from "../src/pages/ConsultorioInvitationPage";
import api from "../src/api/api";

vi.mock("../src/api/api", () => ({ default: { post: vi.fn() } }));

const user = { id: 7, nombre: "Profesional", email: "profesional@example.com", rol: "profesional", activo: true, creado_en: "2026-01-01T00:00:00Z" };

describe("aceptación de invitación a consultorio", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.history.replaceState({}, "", "/invitacion-consultorio#token=secret-invite-token");
    vi.mocked(api.post).mockResolvedValue({ data: {} });
  });

  it("envía el token sólo al endpoint de aceptación y limpia el fragmento tras aceptar", async () => {
    render(<ConsultorioInvitationPage usuario={user} onAutenticado={vi.fn()} />);
    expect(screen.getByText(/profesional@example.com/)).toBeInTheDocument();
    expect(screen.queryByText("secret-invite-token")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Aceptar invitación" }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/consultorios/aceptar-invitacion", { token: "secret-invite-token" }));
    expect(await screen.findByRole("status")).toHaveTextContent("La invitación fue aceptada");
    expect(window.location.hash).toBe("");
  });
});
