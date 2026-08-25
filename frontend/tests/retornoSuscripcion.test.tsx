import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import RetornoSuscripcion from "../src/components/RetornoSuscripcion";
import { obtenerCuentaActual } from "../src/services/cuentaService";
import { sincronizarSuscripcion } from "../src/services/suscripcionService";

vi.mock("../src/services/cuentaService", () => ({ obtenerCuentaActual: vi.fn() }));
vi.mock("../src/services/suscripcionService", () => ({ sincronizarSuscripcion: vi.fn() }));

const cuentaMock = vi.mocked(obtenerCuentaActual);
const sincronizarMock = vi.mocked(sincronizarSuscripcion);
const estadoBase = {
  cuenta_id: 4, plan: "profesional" as const, trial_started_at: "2026-08-01T00:00:00Z",
  trial_ends_at: "2026-08-15T00:00:00Z", billing_provider: "mercadopago" as const,
  provider_status: "authorized", next_payment_at: null, cancelled_at: null,
};

beforeEach(() => {
  vi.clearAllMocks();
  cuentaMock.mockResolvedValue({ cuenta_id: 4, plan: "profesional", subscription_status: "trial", trial_started_at: null, trial_ends_at: null, trial_days_remaining: 0 });
});

it("ignora parámetros falsos y sincroniza la cuenta autenticada", async () => {
  window.history.replaceState({}, "", "/suscripcion/retorno?status=approved&success=true");
  sincronizarMock.mockResolvedValue({ procesado: true, suscripcion: { ...estadoBase, estado: "trial" } });
  render(<RetornoSuscripcion autenticada onIngresar={() => undefined} onVolver={() => undefined} />);
  await waitFor(() => expect(sincronizarMock).toHaveBeenCalledWith(4));
  expect(await screen.findByText("Tu medio de pago quedó asociado.")).toBeInTheDocument();
  expect(screen.getByText(/Todavía no se realizó ningún cobro/)).toBeInTheDocument();
  expect(screen.queryByText(/approved|success|preapproval/i)).not.toBeInTheDocument();
});

it("presenta active sin exponer IDs del proveedor", async () => {
  sincronizarMock.mockResolvedValue({ procesado: true, suscripcion: { ...estadoBase, estado: "active", mp_preapproval_id: "no-debe-mostrarse" } as never });
  render(<RetornoSuscripcion autenticada onIngresar={() => undefined} onVolver={() => undefined} />);
  expect(await screen.findByText("Tu suscripción está activa.")).toBeInTheDocument();
  expect(screen.queryByText("no-debe-mostrarse")).not.toBeInTheDocument();
});

it("sin sesión no sincroniza y ofrece ingresar", async () => {
  render(<RetornoSuscripcion autenticada={false} onIngresar={() => undefined} onVolver={() => undefined} />);
  expect(screen.getByRole("button", { name: "Ingresar" })).toBeInTheDocument();
  expect(sincronizarMock).not.toHaveBeenCalled();
});

describe.each([502, 503])("error %s", (status) => {
  it("muestra mensaje seguro", async () => {
    const error = { isAxiosError: true, response: { status } };
    cuentaMock.mockResolvedValue({ cuenta_id: 4, plan: "profesional", subscription_status: "trial", trial_started_at: null, trial_ends_at: null, trial_days_remaining: 0 });
    sincronizarMock.mockRejectedValue(error);
    render(<RetornoSuscripcion autenticada onIngresar={() => undefined} onVolver={() => undefined} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/No pudimos verificar/);
    expect(screen.queryByText(/preapproval|Mercado Pago respondió/i)).not.toBeInTheDocument();
  });
});
