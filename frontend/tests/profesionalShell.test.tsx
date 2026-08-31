import { render, screen, within } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import ProfesionalShell from "../src/components/ProfesionalShell";

it("mantiene Pacientes en la navegación profesional desde cualquier sección", () => {
  const accion = vi.fn();
  const { container } = render(<ProfesionalShell
    activo="perfil"
    nombre="Sofía Ramírez"
    tituloTopbar="Mi perfil"
    onAbrirInicio={accion}
    onAbrirAgenda={accion}
    onAbrirPacientes={accion}
    onAbrirDisponibilidad={accion}
    onAbrirPrestaciones={accion}
    onAbrirPerfil={accion}
    onCerrarSesion={accion}
  ><p>Contenido</p></ProfesionalShell>);

  expect(screen.getAllByRole("button", { name: "Pacientes" })).toHaveLength(2);
  const navegacion = screen.getByRole("navigation", { name: "Navegación profesional" });
  expect(within(navegacion).getByRole("button", { name: "Ayuda" })).toBeInTheDocument();
  expect(Array.from(navegacion.querySelectorAll("button")).map((button) => button.textContent?.trim())).toEqual(["Inicio", "Mi agenda", "Pacientes", "Mi disponibilidad", "Mis prestaciones", "Mi perfil", "Ayuda"]);
  within(navegacion).getByRole("button", { name: "Ayuda" }).click();
  expect(window.location.pathname).toBe("/ayuda");
  expect(screen.getAllByText("Turnelia")).toHaveLength(2);
  expect(container.querySelector('.prof-sidebar img[src="/brand/mediturnos-symbol-dark.svg"]')).toBeInTheDocument();
  expect(container.querySelector('.prof-marca-movil img[src="/brand/mediturnos-symbol.svg"]')).toBeInTheDocument();
  expect(container.querySelectorAll(".prof-marca-simbolo[aria-hidden='true']")).toHaveLength(2);
});
