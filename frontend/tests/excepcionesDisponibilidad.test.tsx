import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import axios from "axios";

import ExcepcionesDisponibilidad from "../src/components/ExcepcionesDisponibilidad";
import * as servicio from "../src/services/disponibilidadService";
import type { DisponibilidadExcepcion } from "../src/types/disponibilidad";

vi.mock("../src/services/disponibilidadService", () => ({ obtenerMisExcepciones: vi.fn(), crearMiExcepcion: vi.fn(), eliminarMiExcepcion: vi.fn(), cerrarMiDisponibilidadPorRango: vi.fn(), reabrirMiDisponibilidadPorRango: vi.fn() }));

function item(datos: Partial<DisponibilidadExcepcion> = {}): DisponibilidadExcepcion {
  return { id: 1, profesional_id: 7, fecha: "2026-08-20", tipo: "cierre_dia", hora_inicio: null, hora_fin: null, activa: true, ...datos };
}

beforeEach(() => { vi.clearAllMocks(); vi.mocked(servicio.obtenerMisExcepciones).mockResolvedValue([]); });

describe("excepciones de disponibilidad", () => {
  it("renderiza la sección integrada y su estado vacío", async () => {
    render(<ExcepcionesDisponibilidad />);
    expect(await screen.findByRole("heading", { name: "Cambios puntuales" })).toBeInTheDocument();
    expect(screen.getByText("Sin cambios próximos")).toBeInTheDocument();
  });

  it("crea un cierre con advertencia y bloquea el submit", async () => {
    let resolver!: (valor: DisponibilidadExcepcion) => void;
    vi.mocked(servicio.crearMiExcepcion).mockReturnValue(new Promise((resolve) => { resolver = resolve; }));
    render(<ExcepcionesDisponibilidad />); await screen.findByText("Sin cambios próximos");
    fireEvent.click(screen.getByRole("button", { name: "Cerrar un día" }));
    const dialogo = screen.getByRole("dialog", { name: "Cerrar un día" });
    expect(dialogo).toHaveTextContent("Los turnos ya creados no serán cancelados");
    fireEvent.change(within(dialogo).getByLabelText("Fecha"), { target: { value: "2026-08-20" } });
    fireEvent.click(within(dialogo).getByRole("button", { name: "Confirmar" }));
    expect(within(dialogo).getByRole("button", { name: "Guardando…" })).toBeDisabled();
    resolver(item());
    expect(await screen.findByRole("status")).toHaveTextContent("Día cerrado correctamente");
  });

  it("valida y crea un horario especial", async () => {
    vi.mocked(servicio.crearMiExcepcion).mockResolvedValue(item({ id: 2, fecha: "2026-08-22", tipo: "franja_extraordinaria", hora_inicio: "09:00:00", hora_fin: "13:00:00" }));
    render(<ExcepcionesDisponibilidad />); await screen.findByText("Sin cambios próximos");
    fireEvent.click(screen.getByRole("button", { name: "Agregar horario especial" }));
    const dialogo = screen.getByRole("dialog");
    fireEvent.change(within(dialogo).getByLabelText("Fecha"), { target: { value: "2026-08-22" } });
    fireEvent.change(within(dialogo).getByLabelText("Desde"), { target: { value: "13:00" } });
    fireEvent.change(within(dialogo).getByLabelText("Hasta"), { target: { value: "09:00" } });
    fireEvent.click(within(dialogo).getByRole("button", { name: "Confirmar" }));
    expect(screen.getByRole("alert")).toHaveTextContent("posterior");
    fireEvent.change(within(dialogo).getByLabelText("Desde"), { target: { value: "09:00" } });
    fireEvent.change(within(dialogo).getByLabelText("Hasta"), { target: { value: "13:00" } });
    fireEvent.click(within(dialogo).getByRole("button", { name: "Confirmar" }));
    expect(await screen.findByText("09:00–13:00")).toBeInTheDocument();
  });

  it("ordena próximas excepciones por fecha", async () => {
    vi.mocked(servicio.obtenerMisExcepciones).mockResolvedValue([item({ id: 2, fecha: "2026-09-01" }), item({ id: 1, fecha: "2026-08-20" })]);
    render(<ExcepcionesDisponibilidad />);
    const lista = await screen.findByRole("list");
    expect(within(lista).getAllByRole("listitem")[0]).toHaveTextContent("20 de agosto");
  });

  it("elimina cierres y horarios con confirmación específica", async () => {
    vi.mocked(servicio.obtenerMisExcepciones).mockResolvedValue([item(), item({ id: 2, tipo: "franja_extraordinaria", hora_inicio: "09:00:00", hora_fin: "13:00:00" })]);
    vi.mocked(servicio.eliminarMiExcepcion).mockResolvedValue(item({ activa: false }));
    render(<ExcepcionesDisponibilidad />);
    const reabrir = await screen.findByRole("button", { name: "Reabrir fecha" }); fireEvent.click(reabrir);
    fireEvent.click(within(screen.getByRole("dialog", { name: "Reabrir esta fecha" })).getByRole("button", { name: "Reabrir fecha" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Fecha reabierta");
    fireEvent.click(screen.getByRole("button", { name: "Eliminar horario" }));
    expect(screen.getByRole("dialog", { name: "Eliminar horario especial" })).toBeInTheDocument();
  });

  it("mantiene el diálogo ante error backend", async () => {
    vi.mocked(servicio.crearMiExcepcion).mockRejectedValue(new axios.AxiosError("Conflict", "ERR_BAD_RESPONSE", undefined, undefined, { status: 409, statusText: "Conflict", headers: {}, config: { headers: {} }, data: { detail: "Ya existe un cierre activo para esta fecha." } }));
    render(<ExcepcionesDisponibilidad />); await screen.findByText("Sin cambios próximos");
    fireEvent.click(screen.getByRole("button", { name: "Cerrar un día" }));
    fireEvent.change(screen.getByLabelText("Fecha"), { target: { value: "2026-08-20" } });
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Ya existe un cierre");
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("abre vacaciones, valida fechas y calcula la cantidad de días", async () => {
    render(<ExcepcionesDisponibilidad />); await screen.findByText("Sin cambios próximos");
    fireEvent.click(screen.getByRole("button", { name: "Cargar vacaciones" }));
    const dialogo = screen.getByRole("dialog", { name: "Cargar vacaciones" });
    fireEvent.click(within(dialogo).getByRole("button", { name: "Confirmar" }));
    expect(screen.getByRole("alert")).toHaveTextContent("ambas fechas");
    fireEvent.change(within(dialogo).getByLabelText("Fecha desde"), { target: { value: "2026-09-12" } });
    fireEvent.change(within(dialogo).getByLabelText("Fecha hasta"), { target: { value: "2026-09-20" } });
    expect(screen.getByText("Se cerrarán 9 días para nuevas reservas.")).toBeInTheDocument();
    expect(dialogo).toHaveTextContent("no serán cancelados");
  });

  it("crea vacaciones, informa días existentes y bloquea doble submit", async () => {
    let resolver!: (valor: { creados: number; ya_existentes: number }) => void;
    vi.mocked(servicio.cerrarMiDisponibilidadPorRango).mockReturnValue(new Promise((resolve) => { resolver = resolve; }));
    render(<ExcepcionesDisponibilidad />); await screen.findByText("Sin cambios próximos");
    fireEvent.click(screen.getByRole("button", { name: "Cargar vacaciones" }));
    fireEvent.change(screen.getByLabelText("Fecha desde"), { target: { value: "2026-09-12" } });
    fireEvent.change(screen.getByLabelText("Fecha hasta"), { target: { value: "2026-09-20" } });
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));
    expect(screen.getByRole("button", { name: "Guardando…" })).toBeDisabled();
    resolver({ creados: 6, ya_existentes: 3 });
    expect(await screen.findByRole("status")).toHaveTextContent("Se cerraron 6 días. 3 ya estaban cerrados.");
  });

  it("agrupa cierres consecutivos y reabre el período sin tocar horarios especiales", async () => {
    vi.mocked(servicio.obtenerMisExcepciones).mockResolvedValue([
      item({ id: 1, fecha: "2026-09-12" }), item({ id: 2, fecha: "2026-09-13" }), item({ id: 3, fecha: "2026-09-14" }),
      item({ id: 4, fecha: "2026-09-13", tipo: "franja_extraordinaria", hora_inicio: "17:00:00", hora_fin: "19:00:00" }),
    ]);
    vi.mocked(servicio.reabrirMiDisponibilidadPorRango).mockResolvedValue({ reabiertos: 3 });
    render(<ExcepcionesDisponibilidad />);
    expect(await screen.findByText("Período cerrado · 3 días")).toBeInTheDocument();
    expect(screen.getByText("17:00–19:00")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Reabrir período" }));
    const dialogo = screen.getByRole("dialog", { name: "Reabrir período" });
    expect(dialogo).toHaveTextContent("Los horarios especiales existentes no se modificarán");
    fireEvent.click(within(dialogo).getByRole("button", { name: "Reabrir período" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Período reabierto correctamente");
    expect(screen.getByText("17:00–19:00")).toBeInTheDocument();
  });
});
