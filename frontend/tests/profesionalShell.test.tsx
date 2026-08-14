import { render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import ProfesionalShell from "../src/components/ProfesionalShell";

it("mantiene Pacientes en la navegación profesional desde cualquier sección", () => {
  const accion = vi.fn();
  render(<ProfesionalShell
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
});
