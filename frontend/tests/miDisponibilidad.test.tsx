import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import axios from "axios";
import { beforeEach, describe, expect, it, vi } from "vitest";

import MiDisponibilidad from "../src/components/MiDisponibilidad";
import * as disponibilidadService from "../src/services/disponibilidadService";
import * as profesionalService from "../src/services/profesionalService";
import type { Disponibilidad } from "../src/types/disponibilidad";

vi.mock("../src/services/disponibilidadService", () => ({
  crearDisponibilidad: vi.fn(),
  obtenerDisponibilidadesProfesional: vi.fn(),
}));
vi.mock("../src/services/profesionalService", () => ({
  obtenerMiPerfilProfesional: vi.fn(),
}));

const perfil = {
  id: 7,
  nombre: "Sofía",
  apellido: "Ramírez",
  matricula: "MP-DEMO",
  telefono: null,
  email: "sofia@example.com",
  activo: true,
  especialidades: [],
};

function franja(datos: Partial<Disponibilidad> = {}): Disponibilidad {
  return { id: 1, profesional_id: 7, dia_semana: 0, hora_inicio: "08:00:00", hora_fin: "12:00:00", activa: true, ...datos };
}

const acciones = { volver: vi.fn(), agenda: vi.fn(), perfil: vi.fn(), salir: vi.fn() };

function preparar(items: Disponibilidad[] = []) {
  vi.mocked(profesionalService.obtenerMiPerfilProfesional).mockResolvedValue(perfil);
  vi.mocked(disponibilidadService.obtenerDisponibilidadesProfesional).mockResolvedValue(items);
}

function renderizar() {
  return render(<MiDisponibilidad
    nombre="Sofía Ramírez"
    onVolver={acciones.volver}
    onAbrirAgenda={acciones.agenda}
    onAbrirPerfil={acciones.perfil}
    onCerrarSesion={acciones.salir}
  />);
}

beforeEach(() => vi.clearAllMocks());

describe("mi disponibilidad profesional Signature", () => {
  it("muestra los siete días en orden y el shell profesional", async () => {
    preparar();
    renderizar();
    await screen.findByRole("heading", { name: "Tu semana" });
    const semana = screen.getByRole("region", { name: "Tu semana" });
    expect(within(semana).getAllByRole("listitem")).toHaveLength(7);
    expect(within(semana).getAllByRole("heading", { level: 3 }).map((item) => item.textContent)).toEqual([
      "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo",
    ]);
    expect(screen.getByRole("navigation", { name: "Navegación profesional" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Mi disponibilidad" })[0]).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("navigation", { name: "Navegación principal" })).toBeInTheDocument();
    expect(screen.getByText(/semana habitual/i)).toBeInTheDocument();
    expect(screen.getByText("Configurá los días y horarios en los que atendés normalmente cada semana.")).toBeInTheDocument();
    expect(screen.getByText(/nuevo horario habitual/i)).toBeInTheDocument();
  });

  it("ordena franjas y conserva múltiples entidades por día", async () => {
    preparar([
      franja({ id: 3, dia_semana: 2, hora_inicio: "15:00:00", hora_fin: "18:00:00" }),
      franja({ id: 2, dia_semana: 0, hora_inicio: "14:00:00", hora_fin: "19:00:00" }),
      franja({ id: 1, dia_semana: 0, hora_inicio: "08:00:00", hora_fin: "12:00:00" }),
    ]);
    renderizar();
    const semana = await screen.findByRole("region", { name: "Tu semana" });
    const lunes = within(semana).getByRole("heading", { name: "Lunes" }).closest("li")!;
    expect(within(lunes).getAllByText(/08:00–12:00|14:00–19:00/).map((item) => item.textContent)).toEqual(["08:00–12:00", "14:00–19:00"]);
    expect(within(lunes).getByText("Mañana")).toBeInTheDocument();
    expect(within(lunes).getByText("Tarde")).toBeInTheDocument();
    expect(within(semana).getByRole("heading", { name: "Martes" }).closest("li")).toHaveTextContent("Sin disponibilidad");
  });

  it("clasifica las franjas como mañana, tarde y noche según la hora de inicio", async () => {
    preparar([
      franja({ id: 1, hora_inicio: "08:00:00", hora_fin: "12:00:00" }),
      franja({ id: 2, hora_inicio: "14:00:00", hora_fin: "19:00:00" }),
      franja({ id: 3, hora_inicio: "20:00:00", hora_fin: "22:00:00" }),
    ]);
    renderizar();
    const lunes = (await screen.findByRole("heading", { name: "Lunes" })).closest("li")!;
    expect(within(lunes).getByText("Mañana")).toBeInTheDocument();
    expect(within(lunes).getByText("Tarde")).toBeInTheDocument();
    expect(within(lunes).getByText("Noche")).toBeInTheDocument();
  });

  it("preselecciona el día y abre el único formulario", async () => {
    preparar();
    renderizar();
    const jueves = (await screen.findByRole("heading", { name: "Jueves" })).closest("li")!;
    fireEvent.click(within(jueves).getByRole("button", { name: "Agregar franja" }));
    expect(screen.getByLabelText("Día")).toHaveValue("3");
    expect(screen.getByRole("button", { name: "Cerrar formulario" })).toHaveAttribute("aria-expanded", "true");
  });

  it("valida que la hora final sea posterior y enfoca el campo", async () => {
    preparar();
    renderizar();
    await screen.findByRole("heading", { name: "Tu semana" });
    fireEvent.change(screen.getByLabelText("Desde"), { target: { value: "12:00" } });
    fireEvent.change(screen.getByLabelText("Hasta"), { target: { value: "08:00" } });
    fireEvent.click(screen.getAllByRole("button", { name: "Agregar franja" }).at(-1)!);
    expect(screen.getByRole("alert")).toHaveTextContent("La hora de finalización debe ser posterior");
    expect(screen.getByLabelText("Hasta")).toHaveFocus();
    expect(disponibilidadService.crearDisponibilidad).not.toHaveBeenCalled();
  });

  it("bloquea controles y evita doble envío mientras guarda", async () => {
    preparar();
    let resolver!: (valor: Disponibilidad) => void;
    vi.mocked(disponibilidadService.crearDisponibilidad).mockReturnValue(new Promise((resolve) => { resolver = resolve; }));
    renderizar();
    await screen.findByRole("heading", { name: "Tu semana" });
    fireEvent.change(screen.getByLabelText("Desde"), { target: { value: "08:00" } });
    fireEvent.change(screen.getByLabelText("Hasta"), { target: { value: "12:00" } });
    const boton = screen.getAllByRole("button", { name: "Agregar franja" }).at(-1)!;
    fireEvent.click(boton);
    expect(screen.getByRole("button", { name: "Guardando…" })).toBeDisabled();
    expect(screen.getByLabelText("Día")).toBeDisabled();
    expect(screen.getByLabelText("Desde")).toBeDisabled();
    expect(screen.getByLabelText("Hasta")).toBeDisabled();
    fireEvent.submit(screen.getByLabelText("Día").closest("form")!);
    expect(disponibilidadService.crearDisponibilidad).toHaveBeenCalledTimes(1);
    resolver(franja());
    await screen.findByRole("status");
  });

  it("muestra el detalle 409 y conserva los valores", async () => {
    preparar();
    vi.mocked(disponibilidadService.crearDisponibilidad).mockRejectedValue(new axios.AxiosError(
      "Conflict", "ERR_BAD_RESPONSE", undefined, undefined,
      { status: 409, statusText: "Conflict", headers: {}, config: { headers: {} }, data: { detail: "La disponibilidad se solapa con otro horario activo del profesional para el mismo día." } },
    ));
    renderizar();
    await screen.findByRole("heading", { name: "Tu semana" });
    fireEvent.change(screen.getByLabelText("Desde"), { target: { value: "08:00" } });
    fireEvent.change(screen.getByLabelText("Hasta"), { target: { value: "12:00" } });
    fireEvent.click(screen.getAllByRole("button", { name: "Agregar franja" }).at(-1)!);
    expect(await screen.findByRole("alert")).toHaveTextContent("se solapa con otro horario activo");
    expect(screen.getByLabelText("Desde")).toHaveValue("08:00");
    expect(screen.getByLabelText("Hasta")).toHaveValue("12:00");
  });

  it("inserta ordenado y muestra feedback de éxito", async () => {
    preparar([franja({ id: 2, hora_inicio: "14:00:00", hora_fin: "18:00:00" })]);
    vi.mocked(disponibilidadService.crearDisponibilidad).mockResolvedValue(franja());
    renderizar();
    await screen.findByRole("heading", { name: "Tu semana" });
    fireEvent.change(screen.getByLabelText("Desde"), { target: { value: "08:00" } });
    fireEvent.change(screen.getByLabelText("Hasta"), { target: { value: "12:00" } });
    fireEvent.click(screen.getAllByRole("button", { name: "Agregar franja" }).at(-1)!);
    expect(await screen.findByRole("status")).toHaveTextContent("Franja agregada correctamente");
    const lunes = screen.getByRole("heading", { name: "Lunes" }).closest("li")!;
    expect(within(lunes).getAllByText(/08:00–12:00|14:00–18:00/).map((item) => item.textContent)).toEqual(["08:00–12:00", "14:00–18:00"]);
  });

  it("mantiene los siete días en el empty state", async () => {
    preparar([]);
    renderizar();
    expect(await screen.findByRole("heading", { name: "Configurá tu primera franja de atención." })).toBeInTheDocument();
    expect(screen.getAllByText("Sin disponibilidad")).toHaveLength(7);
    expect(screen.getByText((_, elemento) => elemento?.tagName === "P" && elemento.textContent === "0 días configurados")).toBeInTheDocument();
  });

  it("muestra error de carga y permite reintentar", async () => {
    vi.mocked(profesionalService.obtenerMiPerfilProfesional).mockRejectedValueOnce(new Error("red"));
    renderizar();
    expect(await screen.findByRole("alert")).toHaveTextContent("No pudimos cargar tu disponibilidad");
    preparar([]);
    fireEvent.click(screen.getByRole("button", { name: "Reintentar" }));
    await waitFor(() => expect(profesionalService.obtenerMiPerfilProfesional).toHaveBeenCalledTimes(2));
    expect(await screen.findByRole("heading", { name: "Tu semana" })).toBeInTheDocument();
  });
});
