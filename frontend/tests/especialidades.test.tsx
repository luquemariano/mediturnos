import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Especialidades from "../src/components/Especialidades";
import * as servicio from "../src/services/especialidadService";

vi.mock("../src/services/especialidadService", () => ({ obtenerEspecialidades: vi.fn(), crearEspecialidad: vi.fn(), actualizarEspecialidad: vi.fn() }));

const item = { id: 4, nombre: "Cardiología", descripcion: "Atención cardiovascular", duracion_turno_minutos: 45, activa: true };

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(servicio.obtenerEspecialidades).mockResolvedValue([item]);
  vi.mocked(servicio.crearEspecialidad).mockResolvedValue({ ...item, id: 9, nombre: "Dermatología" });
  vi.mocked(servicio.actualizarEspecialidad).mockResolvedValue({ ...item, nombre: "Cardiología clínica" });
  document.body.style.overflow = "";
});

describe("modal de especialidades", () => {
  it("no renderiza el formulario inline antes de abrir y usa portal al abrir", async () => {
    render(<Especialidades onVolver={vi.fn()} />);
    await screen.findByText("Cardiología");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Nueva especialidad" }));
    const modal = await screen.findByRole("dialog");
    expect(modal.closest(".modal-overlay")?.parentElement).toBe(document.body);
    expect(document.body.style.overflow).toBe("hidden");
    expect(within(modal).getByLabelText("Nombre *")).toBeInTheDocument();
    expect(within(modal).getByLabelText("Duración predeterminada (minutos) *")).toBeInTheDocument();
    expect(within(modal).getByLabelText("Descripción")).toBeInTheDocument();
  });

  it("cierra con X y restaura el scroll del body", async () => {
    render(<Especialidades onVolver={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Nueva especialidad" }));
    fireEvent.click(screen.getByRole("button", { name: "Cerrar formulario" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(document.body.style.overflow).toBe("");
  });

  it("cierra con Cancelar", async () => {
    render(<Especialidades onVolver={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Nueva especialidad" }));
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("crea una especialidad desde el modal", async () => {
    render(<Especialidades onVolver={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Nueva especialidad" }));
    const modal = screen.getByRole("dialog");
    fireEvent.change(within(modal).getByLabelText("Nombre *"), { target: { value: "Dermatología" } });
    fireEvent.change(within(modal).getByLabelText("Descripción"), { target: { value: "Piel" } });
    fireEvent.click(within(modal).getByRole("button", { name: "Guardar especialidad" }));
    await waitFor(() => expect(servicio.crearEspecialidad).toHaveBeenCalledWith({ nombre: "Dermatología", descripcion: "Piel", duracion_turno_minutos: 30 }));
    expect(await screen.findByText("Dermatología fue registrada correctamente.")).toBeInTheDocument();
  });

  it("reutiliza el modal para editar", async () => {
    render(<Especialidades onVolver={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Editar" }));
    const modal = await screen.findByRole("dialog");
    expect(within(modal).getByRole("heading", { name: "Editar especialidad" })).toBeInTheDocument();
    fireEvent.change(within(modal).getByLabelText("Nombre *"), { target: { value: "Cardiología clínica" } });
    fireEvent.click(within(modal).getByRole("button", { name: "Guardar cambios" }));
    await waitFor(() => expect(servicio.actualizarEspecialidad).toHaveBeenCalled());
  });

  it("mantiene las validaciones existentes", async () => {
    render(<Especialidades onVolver={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Nueva especialidad" }));
    const modal = screen.getByRole("dialog");
    fireEvent.change(within(modal).getByLabelText("Nombre *"), { target: { value: "A" } });
    fireEvent.click(within(modal).getByRole("button", { name: "Guardar especialidad" }));
    expect(await within(modal).findByRole("alert")).toHaveTextContent("Completá correctamente");
    expect(servicio.crearEspecialidad).not.toHaveBeenCalled();
  });
});
