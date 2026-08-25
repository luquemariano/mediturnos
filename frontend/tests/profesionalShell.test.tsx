import { render, screen } from "@testing-library/react";
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
  expect(screen.getAllByText("Turnelia")).toHaveLength(2);
  expect(container.querySelector('.prof-sidebar img[src="/brand/mediturnos-symbol-dark.svg"]')).toBeInTheDocument();
  expect(container.querySelector('.prof-marca-movil img[src="/brand/mediturnos-symbol.svg"]')).toBeInTheDocument();
  expect(container.querySelectorAll(".prof-marca-simbolo[aria-hidden='true']")).toHaveLength(2);
});
