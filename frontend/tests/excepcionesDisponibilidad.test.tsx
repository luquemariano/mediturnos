import { fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import axios from "axios";

import ExcepcionesDisponibilidad from "../src/components/ExcepcionesDisponibilidad";
import * as servicio from "../src/services/disponibilidadService";
import type { DisponibilidadExcepcion } from "../src/types/disponibilidad";

vi.mock("../src/services/disponibilidadService", () => ({ obtenerMisExcepciones: vi.fn(), crearMiExcepcion: vi.fn(), eliminarMiExcepcion: vi.fn(), cerrarMiDisponibilidadPorRango: vi.fn(), reabrirMiDisponibilidadPorRango: vi.fn(), crearMiFeriado: vi.fn(), eliminarMiFeriado: vi.fn() }));

function item(datos: Partial<DisponibilidadExcepcion> = {}): DisponibilidadExcepcion {
  return { id: 1, profesional_id: 7, fecha: "2026-08-20", tipo: "cierre_dia", origen: "manual", nombre: null, hora_inicio: null, hora_fin: null, activa: true, ...datos };
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.setSystemTime(new Date("2026-08-22T12:00:00-03:00"));
  vi.mocked(servicio.obtenerMisExcepciones).mockResolvedValue([]);
});

afterEach(() => { vi.useRealTimers(); });

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
    fireEvent.change(within(dialogo).getByLabelText("Fecha"), { target: { value: "2026-08-25" } });
    fireEvent.click(within(dialogo).getByRole("button", { name: "Confirmar" }));
    expect(await within(dialogo).findByRole("button", { name: "Guardando…" })).toBeDisabled();
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
    fireEvent.change(screen.getByLabelText("Fecha"), { target: { value: "2026-08-25" } });
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
      item({ id: 1, fecha: "2026-09-12", origen: "vacaciones" }), item({ id: 2, fecha: "2026-09-13", origen: "vacaciones" }), item({ id: 3, fecha: "2026-09-14", origen: "vacaciones" }),
      item({ id: 4, fecha: "2026-09-13", tipo: "franja_extraordinaria", hora_inicio: "17:00:00", hora_fin: "19:00:00" }),
    ]);
    vi.mocked(servicio.reabrirMiDisponibilidadPorRango).mockResolvedValue({ reabiertos: 3 });
    render(<ExcepcionesDisponibilidad />);
    expect(await screen.findByText("Vacaciones · 3 días")).toBeInTheDocument();
    expect(screen.getByText("17:00–19:00")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Reabrir período" }));
    const dialogo = screen.getByRole("dialog", { name: "Reabrir período" });
    expect(dialogo).toHaveTextContent("Los horarios especiales existentes no se modificarán");
    fireEvent.click(within(dialogo).getByRole("button", { name: "Reabrir período" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Período reabierto correctamente");
    expect(screen.getByText("17:00–19:00")).toBeInTheDocument();
  });

  it("crea y muestra un feriado con nombre opcional y advertencia", async () => {
    vi.mocked(servicio.crearMiFeriado).mockResolvedValue(item({ id: 9, origen: "feriado", nombre: "San Martín" }));
    render(<ExcepcionesDisponibilidad />); await screen.findByText("Sin cambios próximos");
    fireEvent.click(screen.getByRole("button", { name: "Agregar feriado" }));
    const dialogo = screen.getByRole("dialog", { name: "Agregar feriado" });
    expect(dialogo).toHaveTextContent("Los turnos ya creados para esta fecha no serán cancelados");
    fireEvent.click(within(dialogo).getByRole("button", { name: "Confirmar" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Seleccioná una fecha");
    fireEvent.change(within(dialogo).getByLabelText("Fecha del feriado"), { target: { value: "2026-08-25" } });
    fireEvent.change(within(dialogo).getByLabelText("Nombre o motivo"), { target: { value: "San Martín" } });
    fireEvent.click(within(dialogo).getByRole("button", { name: "Confirmar" }));
    expect(await screen.findByText("San Martín")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Feriado agregado correctamente");
  });

  it("muestra día no laborable, permite horario especial y quita sólo la marca", async () => {
    vi.mocked(servicio.obtenerMisExcepciones).mockResolvedValue([
      item({ id: 10, origen: "no_laborable", nombre: "Asueto local" }),
      item({ id: 11, tipo: "franja_extraordinaria", hora_inicio: "10:00:00", hora_fin: "12:00:00" }),
    ]);
    vi.mocked(servicio.eliminarMiFeriado).mockResolvedValue(item({ id: 10, origen: "no_laborable", activa: false }));
    render(<ExcepcionesDisponibilidad />);
    expect(await screen.findByText("Día no laborable")).toBeInTheDocument();
    expect(screen.getByText("10:00–12:00")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Quitar feriado" }));
    const dialogo = screen.getByRole("dialog", { name: "Quitar feriado" });
    expect(dialogo).toHaveTextContent("Si existe otro cierre para la fecha, permanecerá cerrada");
    fireEvent.click(within(dialogo).getByRole("button", { name: "Quitar feriado" }));
    expect(await screen.findByRole("status")).toHaveTextContent("Feriado eliminado correctamente");
    expect(screen.getByText("10:00–12:00")).toBeInTheDocument();
  });
});
