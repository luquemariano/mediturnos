import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SistemaTurnosPage from "../src/landing/SistemaTurnosPage";

vi.mock("../src/analytics", () => ({ trackEvent: vi.fn() }));
import { trackEvent } from "../src/analytics";

describe("landing de sistema de turnos", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renderiza el H1, FAQ, CTA y enlace a la gestión integral", () => {
    render(<SistemaTurnosPage />);
    expect(screen.getByRole("heading", { level: 1, name: "Sistema de turnos para organizar tu agenda profesional" })).toBeInTheDocument();
    expect(screen.getByText("¿Qué es un sistema de turnos para consultorios?")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "Probar Turnelia" })[0]).toHaveAttribute("href", "/registro");
    expect(screen.getAllByRole("link", { name: "Gestión integral" })[0]).toHaveAttribute("href", "/software-para-consultorios");
  });

  it("mide el click real del CTA con el source de sistema de turnos", () => {
    render(<SistemaTurnosPage />);
    fireEvent.click(screen.getAllByRole("link", { name: "Probar Turnelia" })[0]);
    expect(trackEvent).toHaveBeenCalledExactlyOnceWith("sign_up_click", { source: "sistema_turnos" });
  });
});
