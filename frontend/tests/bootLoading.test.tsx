import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import BootLoadingScreen from "../src/components/BootLoadingScreen";

const steps = [
  { id: "login", label: "Iniciando sesión", status: "complete" as const },
  { id: "account", label: "Validando tu cuenta", status: "loading" as const },
  { id: "space", label: "Preparando tu espacio", status: "pending" as const },
];

describe("BootLoadingScreen", () => {
  it("representa sólo el estado real de cada etapa", () => {
    render(<BootLoadingScreen steps={steps} prolonged={false} />);
    expect(screen.getByText("Iniciando sesión").previousElementSibling).toHaveTextContent("✓");
    expect(screen.getByText("Validando tu cuenta").previousElementSibling).not.toHaveTextContent("✓");
    expect(screen.getByText("Preparando tu espacio").previousElementSibling).toHaveTextContent("");
  });

  it("muestra la espera prolongada sin agregar una etapa ficticia", () => {
    render(<BootLoadingScreen steps={steps.slice(1)} prolonged />);
    expect(screen.getByText(/Estamos tardando un poco más/)).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
  });

  it("permite reintentar y muestra el error amigable", () => {
    const retry = vi.fn();
    render(<BootLoadingScreen steps={steps} prolonged={true} error="No pudimos completar el ingreso." onRetry={retry} />);
    fireEvent.click(screen.getByRole("button", { name: "Intentar nuevamente" }));
    expect(retry).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("listitem")).not.toBeInTheDocument();
  });
});
