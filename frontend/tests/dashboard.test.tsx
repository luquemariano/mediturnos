import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import Dashboard from "../src/components/Dashboard";

function renderizar(rol: string) {
  const accion = vi.fn();
  render(<Dashboard nombre="Usuario" rol={rol} onAbrirPacientes={accion} onAbrirProfesionales={accion} onAbrirEspecialidades={accion} onAbrirPrestaciones={accion} onAbrirTurnos={accion} onAbrirDisponibilidades={accion} onAbrirPerfil={accion} onAbrirCuentas={accion} onCerrarSesion={accion} />);
}

describe("dashboard por rol", () => {
  it("muestra solo módulos globales al administrador", () => {
    renderizar("administrador");
    expect(screen.getByRole("heading", { name: "Panel administrativo" })).toBeInTheDocument();
    expect(screen.getByText("Gestioná cuentas, profesionales y el catálogo global de Turnelia.")).toBeInTheDocument();
    for (const nombre of ["Cuentas", "Profesionales", "Especialidades"]) expect(screen.getByRole("button", { name: new RegExp(nombre) })).toBeInTheDocument();
    for (const nombre of ["Pacientes", "Prestaciones", "Turnos", "Disponibilidades", "Pagos"]) expect(screen.queryByRole("button", { name: new RegExp(nombre) })).not.toBeInTheDocument();
  });
  it("limita el dashboard de recepcionista a sus módulos autorizados", () => {
    renderizar("recepcionista");
    expect(screen.getByRole("button", { name: /Pacientes/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Turnos/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Profesionales/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Especialidades/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Cuentas/ })).not.toBeInTheDocument();
  });
  it("muestra el recorrido propio del profesional sin enlaces administrativos", () => {
    renderizar("profesional");
    expect(screen.getByRole("button", { name: /Mi agenda/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Mi disponibilidad/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Mi perfil/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Pacientes/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Turnos/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Cuentas/ })).not.toBeInTheDocument();
  });
  it("muestra el recorrido propio del paciente sin enlaces administrativos", () => {
    renderizar("paciente");
    expect(screen.getByRole("button", { name: /Mis turnos/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Mi perfil/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Pacientes/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Disponibilidades/ })).not.toBeInTheDocument();
  });
});
