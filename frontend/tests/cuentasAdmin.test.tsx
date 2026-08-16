import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CuentasAdmin from "../src/components/CuentasAdmin";
import * as servicio from "../src/services/adminCuentaService";
import type { CuentaAdminDetalle, CuentaAdminItem, CuentasAdminPagina, CuentasAdminResumen } from "../src/types/adminCuenta";

vi.mock("../src/services/adminCuentaService", () => ({ obtenerCuentasAdmin: vi.fn(), obtenerResumenCuentasAdmin: vi.fn(), obtenerDetalleCuentaAdmin: vi.fn(), obtenerHistorialCuentaAdmin: vi.fn(), activarSuscripcionAdmin: vi.fn(), reactivarSuscripcionAdmin: vi.fn(), marcarPagoPendienteAdmin: vi.fn(), cancelarSuscripcionAdmin: vi.fn(), extenderTrialAdmin: vi.fn(), cambiarPlanAdmin: vi.fn() }));

const item: CuentaAdminItem = { cuenta_id: 7, nombre: "Consultorio Ana", tipo: "individual", plan: "profesional", estado: "trial", created_at: "2026-08-10T12:00:00Z", trial_ends_at: "2026-08-29T12:00:00Z", profesionales_count: 1, miembros_count: 1, profesional_principal: { profesional_id: 4, nombre: "Ana", apellido: "Pérez", matricula: "MP-100", email: "ana@test.com" } };
const pagina: CuentasAdminPagina = { items: [item], total: 1, offset: 0, limit: 25 };
const resumen: CuentasAdminResumen = { cuentas_totales: 6, trials_activos: 2, suscripciones_activas: 3, trials_finalizados: 1, altas_ultimos_30_dias: 4 };
const detalle: CuentaAdminDetalle = { cuenta: { id: 7, nombre: "Consultorio Ana", tipo: "individual", created_at: item.created_at, updated_at: item.created_at }, suscripcion: { plan: "profesional", estado: "trial", estado_persistido: null, trial_started_at: "2026-08-15T12:00:00Z", trial_ends_at: item.trial_ends_at, trial_days_remaining: 14 }, miembros: [{ usuario_id: 2, nombre: "Ana Dueña", email: "ana@test.com", rol_cuenta: "propietario", activo: true, miembro_desde: item.created_at }], profesionales: [{ id: 4, nombre: "Ana", apellido: "Pérez", matricula: "MP-100", email: "ana@test.com", activo: true }] };

function preparar() { vi.mocked(servicio.obtenerResumenCuentasAdmin).mockResolvedValue(resumen); vi.mocked(servicio.obtenerCuentasAdmin).mockResolvedValue(pagina); vi.mocked(servicio.obtenerDetalleCuentaAdmin).mockResolvedValue(detalle); vi.mocked(servicio.obtenerHistorialCuentaAdmin).mockResolvedValue([]); vi.mocked(servicio.activarSuscripcionAdmin).mockResolvedValue({ ...detalle, suscripcion: { ...detalle.suscripcion!, estado: "active" } }); }

beforeEach(() => { vi.clearAllMocks(); preparar(); });

describe("panel administrativo de cuentas", () => {
  it("muestra métricas, tabla, badges y alternativa móvil", async () => {
    render(<CuentasAdmin onVolver={vi.fn()} />);
    expect(await screen.findByText("Cuentas totales")).toBeInTheDocument();
    expect(screen.getByText("6")).toBeInTheDocument();
    expect(await screen.findAllByText("Consultorio Ana")).toHaveLength(2);
    expect(screen.getAllByText("Prueba gratuita").length).toBeGreaterThan(0);
    expect(document.querySelector(".cuentas-mobile-lista")).toBeInTheDocument();
    expect(document.querySelector(".cuenta-mobile-card")).toBeInTheDocument();
  });

  it("aplica búsqueda y filtros con offset reiniciado", async () => {
    render(<CuentasAdmin onVolver={vi.fn()} />);
    await screen.findAllByText("Consultorio Ana");
    fireEvent.change(screen.getByLabelText("Buscar"), { target: { value: "ana" } });
    fireEvent.change(screen.getByLabelText("Estado"), { target: { value: "active" } });
    fireEvent.change(screen.getByLabelText("Plan"), { target: { value: "centro" } });
    await waitFor(() => expect(servicio.obtenerCuentasAdmin).toHaveBeenLastCalledWith(expect.objectContaining({ q: "ana", estado: "active", plan: "centro", offset: 0, limit: 25 }), expect.any(AbortSignal)), { timeout: 1500 });
  });

  it("pagina hacia adelante", async () => {
    vi.mocked(servicio.obtenerCuentasAdmin).mockResolvedValue({ ...pagina, total: 30 });
    render(<CuentasAdmin onVolver={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: "Siguiente" }));
    await waitFor(() => expect(servicio.obtenerCuentasAdmin).toHaveBeenLastCalledWith(expect.objectContaining({ offset: 25 }), expect.any(AbortSignal)), { timeout: 1500 });
  });

  it("muestra loading y estado vacío", async () => {
    let resolver!: (valor: CuentasAdminPagina) => void;
    vi.mocked(servicio.obtenerCuentasAdmin).mockReturnValue(new Promise(resolve => { resolver = resolve; }));
    render(<CuentasAdmin onVolver={vi.fn()} />);
    expect(await screen.findByLabelText("Cargando cuentas")).toBeInTheDocument();
    resolver({ ...pagina, items: [], total: 0 });
    expect(await screen.findByRole("heading", { name: "No encontramos cuentas" })).toBeInTheDocument();
  });

  it("aísla el error de métricas y permite reintentar", async () => {
    vi.mocked(servicio.obtenerResumenCuentasAdmin).mockRejectedValueOnce(new Error("red"));
    render(<CuentasAdmin onVolver={vi.fn()} />);
    expect((await screen.findAllByText("Consultorio Ana")).length).toBeGreaterThan(0);
    const error = await screen.findByRole("alert");
    expect(error).toHaveTextContent("No pudimos cargar las métricas.");
    vi.mocked(servicio.obtenerResumenCuentasAdmin).mockResolvedValueOnce(resumen);
    fireEvent.click(within(error).getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByText("Cuentas totales")).toBeInTheDocument();
  });

  it("muestra error de listado y reintenta", async () => {
    vi.mocked(servicio.obtenerCuentasAdmin).mockRejectedValueOnce(new Error("red"));
    render(<CuentasAdmin onVolver={vi.fn()} />);
    const error = await screen.findByText("No pudimos cargar las cuentas.", {}, { timeout: 1500 });
    fireEvent.click(within(error.parentElement!).getByRole("button", { name: "Reintentar" }));
    expect((await screen.findAllByText("Consultorio Ana", {}, { timeout: 1500 })).length).toBeGreaterThan(0);
  });

  it("abre y cierra el detalle comercial", async () => {
    render(<CuentasAdmin onVolver={vi.fn()} />);
    fireEvent.click((await screen.findAllByRole("button", { name: "Consultorio Ana" }))[0]);
    const dialogo = await screen.findByRole("dialog");
    expect(within(dialogo).getByText("Ana Dueña")).toBeInTheDocument();
    expect(dialogo).toHaveTextContent("MP-100");
    fireEvent.click(within(dialogo).getByRole("button", { name: "Cerrar detalle" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("representa cuentas sin profesional principal", async () => {
    vi.mocked(servicio.obtenerCuentasAdmin).mockResolvedValue({ ...pagina, items: [{ ...item, profesional_principal: null }] });
    render(<CuentasAdmin onVolver={vi.fn()} />);
    expect((await screen.findAllByText("Sin profesional principal")).length).toBeGreaterThan(0);
  });

  it("muestra acciones válidas para trial y oculta las inválidas", async () => {
    render(<CuentasAdmin onVolver={vi.fn()} />);
    fireEvent.click((await screen.findAllByRole("button", { name: "Consultorio Ana" }))[0]);
    const dialogo = await screen.findByRole("dialog");
    expect(within(dialogo).getByRole("button", { name: "Activar suscripción" })).toBeInTheDocument();
    expect(within(dialogo).getByRole("button", { name: "Extender prueba" })).toBeInTheDocument();
    expect(within(dialogo).queryByRole("button", { name: "Marcar pago pendiente" })).not.toBeInTheDocument();
  });

  it("ejecuta una acción y refresca detalle, listado, métricas e historial", async () => {
    render(<CuentasAdmin onVolver={vi.fn()} />);
    fireEvent.click((await screen.findAllByRole("button", { name: "Consultorio Ana" }))[0]);
    const dialogo = await screen.findByRole("dialog");
    fireEvent.change(within(dialogo).getByLabelText("Motivo (opcional)"), { target: { value: "Pago recibido" } });
    fireEvent.click(within(dialogo).getByRole("button", { name: "Activar suscripción" }));
    await waitFor(() => expect(servicio.activarSuscripcionAdmin).toHaveBeenCalledWith(7, "Pago recibido"));
    await waitFor(() => expect(servicio.obtenerResumenCuentasAdmin).toHaveBeenCalledTimes(2));
    expect(servicio.obtenerHistorialCuentaAdmin).toHaveBeenCalledTimes(2);
  });

  it("muestra historial comercial", async () => {
    vi.mocked(servicio.obtenerHistorialCuentaAdmin).mockResolvedValue([{ id: 1, actor_usuario_id: 1, actor_nombre: "Administrador Demo", actor_tipo: "usuario", accion: "activar", estado_anterior: "trial", estado_nuevo: "active", plan_anterior: null, plan_nuevo: null, motivo: "Pago recibido", created_at: "2026-08-15T23:20:00Z" }]);
    render(<CuentasAdmin onVolver={vi.fn()} />);
    fireEvent.click((await screen.findAllByRole("button", { name: "Consultorio Ana" }))[0]);
    expect(await screen.findByText("Administrador Demo")).toBeInTheDocument();
    expect(screen.getByText("Pago recibido")).toBeInTheDocument();
  });
});
