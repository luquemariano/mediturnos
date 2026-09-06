import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SoftwareConsultoriosPage from "../src/landing/SoftwareConsultoriosPage";

vi.mock("../src/analytics", () => ({ trackEvent: vi.fn() }));
import { trackEvent } from "../src/analytics";

describe("landing de software para consultorios", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renderiza la propuesta, funciones, FAQ visible y CTAs de registro", () => {
    render(<SoftwareConsultoriosPage />);
    expect(screen.getByRole("heading", { level: 1, name: "Software para consultorios simple y completo" })).toBeInTheDocument();
    expect(screen.getByText("Agenda profesional")).toBeInTheDocument();
    expect(screen.getByText("¿Qué es un software para consultorios?")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "Probar Turnelia" })[0]).toHaveAttribute("href", "/registro");
    expect(screen.getAllByRole("link", { name: "Centro de Ayuda" })[0]).toHaveAttribute("href", "/ayuda");
  });

  it("mide el click real del CTA con el source de la landing", () => {
    render(<SoftwareConsultoriosPage />);
    fireEvent.click(screen.getAllByRole("link", { name: "Probar Turnelia" })[0]);
    expect(trackEvent).toHaveBeenCalledExactlyOnceWith("sign_up_click", { source: "software_consultorios" });
  });
});
