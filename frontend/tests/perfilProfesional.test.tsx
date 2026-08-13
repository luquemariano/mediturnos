import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import PerfilPropio from "../src/components/PerfilPropio";
import * as especialidadService from "../src/services/especialidadService";
import * as pacienteService from "../src/services/pacienteService";
import * as profesionalService from "../src/services/profesionalService";
import type { Especialidad } from "../src/types/especialidad";
import type { Paciente } from "../src/types/paciente";
import type { Profesional } from "../src/types/profesional";

vi.mock("../src/services/especialidadService", () => ({ obtenerEspecialidades: vi.fn() }));
vi.mock("../src/services/pacienteService", () => ({ obtenerMiPerfilPaciente: vi.fn() }));
vi.mock("../src/services/profesionalService", () => ({ obtenerMiPerfilProfesional: vi.fn() }));

const perfil: Profesional = {
  id: 7,
  nombre: "Sofía",
  apellido: "Ramírez",
  matricula: "MP-DEMO-PSIQ-001",
  telefono: "11 4567-8901",
  email: "sofia@mediturnos.com.ar",
  activo: true,
  especialidades: [
    { especialidad_id: 3, duracion_turno_minutos: 50 },
    { especialidad_id: 4, duracion_turno_minutos: null },
  ],
};

const especialidades: Especialidad[] = [
  { id: 3, nombre: "Psicología", descripcion: null, duracion_turno_minutos: 45, activa: true },
  { id: 4, nombre: "Psicoterapia", descripcion: null, duracion_turno_minutos: 60, activa: true },
];

const paciente: Paciente = {
  id: 8,
  nombre: "Juan",
  apellido: "Pérez",
  dni: "30111222",
  fecha_nacimiento: null,
  telefono: "11 4000-0000",
  email: "juan@example.com",
  obra_social: null,
  numero_afiliado: null,
  activo: true,
};

const acciones = {
  inicio: vi.fn(),
  agenda: vi.fn(),
  disponibilidad: vi.fn(),
  perfil: vi.fn(),
  salir: vi.fn(),
};

function renderizarProfesional() {
  return render(<PerfilPropio
    tipo="profesional"
    nombre="Sofía"
    onVolver={acciones.inicio}
    onAbrirAgenda={acciones.agenda}
    onAbrirDisponibilidad={acciones.disponibilidad}
    onAbrirPerfil={acciones.perfil}
    onCerrarSesion={acciones.salir}
  />);
}

function preparar(perfilActual: Profesional = perfil) {
  vi.mocked(profesionalService.obtenerMiPerfilProfesional).mockResolvedValue(perfilActual);
  vi.mocked(especialidadService.obtenerEspecialidades).mockResolvedValue(especialidades);
}

beforeEach(() => vi.clearAllMocks());

describe("perfil profesional Salud Humana Signature", () => {
  it("muestra shell, identidad, contacto y especialidades reales", async () => {
    preparar();
    renderizarProfesional();

    expect(await screen.findByRole("heading", { name: "Sofía Ramírez" })).toBeInTheDocument();
    expect(screen.getByText((_, elemento) =>
      elemento?.classList.contains("perfil-profesional-matricula") === true
      && elemento.textContent?.includes("MP-DEMO-PSIQ-001") === true,
    )).toBeInTheDocument();
    expect(screen.getByText("sofia@mediturnos.com.ar")).toBeInTheDocument();
    expect(screen.getByText("11 4567-8901")).toBeInTheDocument();
    expect(screen.getByText("Perfil activo")).toBeInTheDocument();
    expect(screen.getByText("Psicología")).toBeInTheDocument();
    expect(screen.getByText("Turnos de 50 minutos")).toBeInTheDocument();
    expect(screen.getByText("Psicoterapia")).toBeInTheDocument();
    expect(screen.queryByText("Turnos de 60 minutos")).not.toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "Navegación profesional" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Mi perfil" })[0]).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("navigation", { name: "Navegación principal" })).toBeInTheDocument();
  });

  it("representa el perfil inactivo sin badge", async () => {
    preparar({ ...perfil, activo: false });
    renderizarProfesional();
    const estado = await screen.findByText("Perfil inactivo");
    expect(estado).toHaveClass("inactivo");
    expect(estado).not.toHaveClass("pill");
  });

  it("usa un fallback técnico cuando falta una especialidad en el catálogo", async () => {
    vi.mocked(profesionalService.obtenerMiPerfilProfesional).mockResolvedValue({
      ...perfil,
      especialidades: [{ especialidad_id: 99, duracion_turno_minutos: null }],
    });
    vi.mocked(especialidadService.obtenerEspecialidades).mockResolvedValue(especialidades);
    renderizarProfesional();
    expect(await screen.findByText("Especialidad no disponible")).toBeInTheDocument();
    expect(screen.queryByText(/Especialidad #99/)).not.toBeInTheDocument();
  });

  it("mantiene el shell visible durante la carga y muestra skeleton estructural", () => {
    vi.mocked(profesionalService.obtenerMiPerfilProfesional).mockReturnValue(new Promise(() => undefined));
    vi.mocked(especialidadService.obtenerEspecialidades).mockReturnValue(new Promise(() => undefined));
    renderizarProfesional();
    expect(screen.getByRole("navigation", { name: "Navegación profesional" })).toBeInTheDocument();
    expect(screen.getByLabelText("Cargando perfil")).toHaveAttribute("aria-busy", "true");
  });

  it("muestra error global y permite reintentar el perfil", async () => {
    vi.mocked(profesionalService.obtenerMiPerfilProfesional).mockRejectedValueOnce(new Error("red"));
    vi.mocked(especialidadService.obtenerEspecialidades).mockResolvedValue(especialidades);
    renderizarProfesional();
    expect(await screen.findByRole("alert")).toHaveTextContent("No pudimos cargar tu perfil.");
    vi.mocked(profesionalService.obtenerMiPerfilProfesional).mockResolvedValueOnce(perfil);
    fireEvent.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByRole("heading", { name: "Sofía Ramírez" })).toBeInTheDocument();
    expect(profesionalService.obtenerMiPerfilProfesional).toHaveBeenCalledTimes(2);
  });

  it("aísla el error de especialidades y permite reintentarlo", async () => {
    vi.mocked(profesionalService.obtenerMiPerfilProfesional).mockResolvedValue(perfil);
    vi.mocked(especialidadService.obtenerEspecialidades).mockRejectedValueOnce(new Error("red"));
    renderizarProfesional();
    expect(await screen.findByRole("heading", { name: "Sofía Ramírez" })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("No pudimos cargar el detalle de tus especialidades.");
    vi.mocked(especialidadService.obtenerEspecialidades).mockResolvedValueOnce(especialidades);
    fireEvent.click(within(screen.getByRole("status")).getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByText("Psicología")).toBeInTheDocument();
    expect(especialidadService.obtenerEspecialidades).toHaveBeenCalledTimes(2);
  });

  it("conecta la navegación y el cierre de sesión del shell", async () => {
    preparar();
    renderizarProfesional();
    await screen.findByRole("heading", { name: "Sofía Ramírez" });
    const navegacion = screen.getByRole("navigation", { name: "Navegación profesional" });
    fireEvent.click(within(navegacion).getByRole("button", { name: "Inicio" }));
    fireEvent.click(within(navegacion).getByRole("button", { name: "Mi agenda" }));
    fireEvent.click(within(navegacion).getByRole("button", { name: "Mi disponibilidad" }));
    fireEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));
    expect(acciones.inicio).toHaveBeenCalled();
    expect(acciones.agenda).toHaveBeenCalled();
    expect(acciones.disponibilidad).toHaveBeenCalled();
    expect(acciones.salir).toHaveBeenCalled();
  });

  it("mantiene la variante paciente sin el shell profesional", async () => {
    vi.mocked(pacienteService.obtenerMiPerfilPaciente).mockResolvedValue(paciente);
    const volver = vi.fn();
    render(<PerfilPropio tipo="paciente" onVolver={volver} />);
    expect(await screen.findByText("Juan Pérez")).toBeInTheDocument();
    expect(screen.getByText("juan@example.com")).toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "Navegación profesional" })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Volver al panel" }));
    expect(volver).toHaveBeenCalled();
  });

  it("muestra valores de contacto no informados", async () => {
    preparar({ ...perfil, email: null, telefono: null });
    renderizarProfesional();
    await screen.findByRole("heading", { name: "Sofía Ramírez" });
    expect(screen.getAllByText("No informado")).toHaveLength(2);
  });
});
