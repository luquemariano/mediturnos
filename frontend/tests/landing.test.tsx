import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LandingPage from "../src/landing/LandingPage";

describe("LandingPage FAQ", () => {
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
});
