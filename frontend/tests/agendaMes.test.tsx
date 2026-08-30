import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import AgendaMes from "../src/components/AgendaMes";
import type { Turno } from "../src/types/turno";

const turno = (id: number, fecha_hora: string, fecha_fin?: string): Turno => ({
  id, paciente_id: id, paciente_nombre: `Paciente ${id}`, prestacion_id: id, prestacion_nombre: "Consulta", profesional_nombre: "Profesional", especialidad_nombre: "Clínica", fecha_hora, fecha_fin, estado: "confirmado", observaciones: null,
});

describe("AgendaMes", () => {
  it("renderiza encabezados, grilla de contexto y conteos", () => {
    render(<AgendaMes fecha="2026-08-15" ahora={new Date("2026-08-15T12:00:00Z")} turnos={[turno(1, "2026-08-15T13:00:00Z"), turno(2, "2026-08-15T14:00:00Z"), turno(3, "2026-09-01T13:00:00Z")]} onSeleccionarDia={vi.fn()} />);
    expect(screen.getAllByRole("columnheader")).toHaveLength(7);
    expect(screen.getAllByRole("button").length).toBe(42);
    expect(screen.getByRole("button", { name: /sábado, 15 de agosto.*2 turnos/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /1 de septiembre.*1 turno/i })).toHaveClass("es-contexto");
  });

  it("marca Hoy y mantiene la etiqueta accesible", () => {
    render(<AgendaMes fecha="2026-09-02" ahora={new Date("2026-09-02T12:00:00Z")} turnos={[]} onSeleccionarDia={vi.fn()} />);
    expect(screen.getByText("Hoy")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Hoy, miércoles, 2 de septiembre/i })).toBeInTheDocument();
  });

  it("selecciona un día de contexto sin cambiar el mes antes de pasar a Día", () => {
    const seleccionar = vi.fn();
    render(<AgendaMes fecha="2026-09-02" ahora={new Date("2026-09-02T12:00:00Z")} turnos={[]} onSeleccionarDia={seleccionar} />);
    fireEvent.click(screen.getByRole("button", { name: /31 de agosto/i }));
    expect(seleccionar).toHaveBeenCalledWith("2026-08-31");
  });
});
