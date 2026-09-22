import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { trackEvent } from "../src/analytics";
import { capturePostHogEvent } from "../src/posthog";
import LandingPage from "../src/landing/LandingPage";

vi.mock("../src/analytics", async () => ({ ...(await vi.importActual<typeof import("../src/analytics")>("../src/analytics")), trackEvent: vi.fn() }));
vi.mock("../src/posthog", async () => ({ ...(await vi.importActual<typeof import("../src/posthog")>("../src/posthog")), capturePostHogEvent: vi.fn() }));

describe("LandingPage FAQ", () => {
  it("comunica recordatorios por email y WhatsApp y enlaza al Centro de Ayuda", () => {
    render(<LandingPage />);
    const recordatorios = document.querySelector("#recordatorios");
    expect(recordatorios).toBeTruthy();
    expect(recordatorios).toHaveTextContent(/email y WhatsApp/);
    expect(recordatorios).toHaveTextContent(/confirma.*cancela/i);
    expect(recordatorios).toHaveTextContent(/lista de espera/i);
    expect(recordatorios?.querySelector('a[href="/ayuda/recordatorios"]')).toHaveTextContent(/cómo funcionan los recordatorios/i);
    expect(recordatorios?.querySelector('[aria-label*="email y WhatsApp"]')).toBeTruthy();
    expect(recordatorios?.querySelectorAll("button")).toHaveLength(0);
    expect(recordatorios).not.toHaveTextContent(/reprogram/i);
    fireEvent.click(recordatorios?.querySelector('a[href="/ayuda/recordatorios"]') as HTMLAnchorElement);
    expect(trackEvent).toHaveBeenCalledWith("help_article_click", { source: "landing_recordatorios" });
    expect(capturePostHogEvent).toHaveBeenCalledWith("help_article_click", { source: "landing_recordatorios" });
  });

  it("renderiza las 11 preguntas cerradas inicialmente", () => {
    render(<LandingPage />);
    const preguntas = screen.getAllByRole("button", { name: /\?/ });
    expect(preguntas).toHaveLength(11);
    preguntas.forEach(pregunta => expect(pregunta).toHaveAttribute("aria-expanded", "false"));
    expect(screen.queryByText(/Turnelia es una plataforma pensada/)).not.toBeVisible();
  });

  it("abre, cierra y reemplaza una respuesta, manteniendo ARIA sincronizado", () => {
    render(<LandingPage />);
    const preguntas = screen.getAllByRole("button", { name: /\?/ });
    fireEvent.click(preguntas[0]);
    expect(preguntas[0]).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText(/Turnelia es una plataforma pensada/)).toBeVisible();

    fireEvent.click(preguntas[0]);
    expect(preguntas[0]).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(preguntas[1]);
    expect(preguntas[1]).toHaveAttribute("aria-expanded", "true");
    expect(preguntas[0]).toHaveAttribute("aria-expanded", "false");
  });

  it("presenta la FAQ de recordatorios con ambos canales y sin reprogramación", () => {
    render(<LandingPage />);
    const pregunta = screen.getByRole("button", { name: "¿Turnelia envía recordatorios de los turnos?" });
    fireEvent.click(pregunta);
    const respuesta = screen.getByText(/recordatorios automáticos por email y WhatsApp/i);
    expect(respuesta).toHaveTextContent(/teléfono válido/i);
    expect(respuesta).toHaveTextContent(/confirmar o cancelar/i);
    expect(respuesta).not.toHaveTextContent(/reprogramación.*disponible/i);
  });
});
