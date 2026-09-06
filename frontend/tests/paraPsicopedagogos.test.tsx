import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ParaPsicopedagogosPage from "../src/landing/ParaPsicopedagogosPage";

vi.mock("../src/analytics", () => ({ trackEvent: vi.fn() }));
import { trackEvent } from "../src/analytics";

describe("landing para psicopedagogos", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renderiza H1, FAQ, CTA y enlaces a las landings relacionadas", () => {
    render(<ParaPsicopedagogosPage />);
    expect(screen.getByRole("heading", { level: 1, name: "Software para psicopedagogos que simplifica tu gestión diaria" })).toBeInTheDocument();
    expect(screen.getByText("¿Qué puede organizar un psicopedagogo con Turnelia?")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "Probar Turnelia" })[0]).toHaveAttribute("href", "/registro");
    expect(screen.getByRole("link", { name: "Gestión integral" })).toHaveAttribute("href", "/software-para-consultorios");
    expect(screen.getByRole("link", { name: "Sistema de turnos" })).toHaveAttribute("href", "/sistema-de-turnos");
  });

  it("mide el click real del CTA con source de psicopedagogos", () => {
    render(<ParaPsicopedagogosPage />);
    fireEvent.click(screen.getAllByRole("link", { name: "Probar Turnelia" })[0]);
    expect(trackEvent).toHaveBeenCalledExactlyOnceWith("sign_up_click", { source: "psicopedagogos" });
  });
});
