import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import ActivarSuscripcion from "../src/components/ActivarSuscripcion";
import { iniciarSuscripcion } from "../src/services/suscripcionService";

let entregarToken: ((token: string) => Promise<void>) | undefined;
let importeMontado = 0;

vi.mock("../src/services/cuentaService", () => ({
  obtenerCuentaActual: vi.fn().mockResolvedValue({
    cuenta_id: 7, plan: "profesional", subscription_status: "trial",
    trial_started_at: "2026-08-01T00:00:00Z",
    trial_ends_at: "2026-08-15T00:00:00Z", trial_days_remaining: 10,
  }),
}));
vi.mock("../src/services/suscripcionService", () => ({
  obtenerSuscripcion: vi.fn().mockResolvedValue({
    cuenta_id: 7, plan: "profesional", estado: "trial",
    trial_started_at: "2026-08-01T00:00:00Z",
    trial_ends_at: "2026-08-15T00:00:00Z", billing_provider: "manual",
    provider_status: null, next_payment_at: null, cancelled_at: null,
  }),
  iniciarSuscripcion: vi.fn(),
}));
vi.mock("../src/services/mercadoPagoCardForm", () => ({
  montarFormularioMercadoPago: vi.fn(async ({ amount, onToken }) => {
    importeMontado = amount;
    entregarToken = onToken;
    return () => undefined;
  }),
}));

const iniciarMock = vi.mocked(iniciarSuscripcion);

beforeEach(() => {
  vi.clearAllMocks();
  entregarToken = undefined;
  importeMontado = 0;
});

afterEach(() => {
  vi.unstubAllEnvs();
});

it("muestra planes y remonta Mercado Pago con el precio seleccionado", async () => {
  render(<ActivarSuscripcion onVolver={() => undefined} />);
  expect(screen.getByText("Facturación y suscripción")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Medio de pago" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Asociar medio de pago" })).toBeInTheDocument();
  await waitFor(() => expect(importeMontado).toBe(34_900));
  fireEvent.click(screen.getByLabelText(/Consultorio/));
  await waitFor(() => expect(importeMontado).toBe(69_900));
  expect(screen.getByText("$149.900/mes")).toBeInTheDocument();
  expect(screen.getByText(/primer cobro se programará/i)).toBeInTheDocument();
});

it("envía sólo plan y token, bloquea mientras procesa y conserva trial", async () => {
  let resolver: ((value: { estado: "trial"; checkout_url: null }) => void) | undefined;
  iniciarMock.mockReturnValue(new Promise((resolve) => { resolver = resolve; }));
  render(<ActivarSuscripcion onVolver={() => undefined} />);
  await waitFor(() => expect(entregarToken).toBeDefined());
  const promesa = entregarToken?.("token-efimero");
  await waitFor(() => expect(screen.getByRole("button", { name: /Procesando/ })).toBeDisabled());
  expect(iniciarMock).toHaveBeenCalledWith(7, "profesional", "token-efimero");
  expect(JSON.stringify(iniciarMock.mock.calls)).not.toContain("411111");
  expect(JSON.stringify(iniciarMock.mock.calls)).not.toContain("cvv");
  resolver?.({ estado: "trial", checkout_url: null });
  await promesa;
  expect(await screen.findByText(/todavía no se realizó ningún cobro/i)).toBeInTheDocument();
});

it("en diagnóstico local muestra el token y no llama al backend", async () => {
  vi.stubEnv("PROD", false);
  vi.stubEnv("VITE_MERCADOPAGO_DEBUG_CARD_TOKEN", "true");
  render(<ActivarSuscripcion onVolver={() => undefined} />);
  await waitFor(() => expect(entregarToken).toBeDefined());

  await entregarToken?.("token-diagnostico");

  expect(await screen.findByLabelText("Card token de diagnóstico")).toHaveTextContent("token-diagnostico");
  expect(iniciarMock).not.toHaveBeenCalled();
});

it("ignora el diagnóstico en producción aunque la variable esté activa", async () => {
  vi.stubEnv("PROD", true);
  vi.stubEnv("VITE_MERCADOPAGO_DEBUG_CARD_TOKEN", "true");
  iniciarMock.mockResolvedValue({ estado: "trial", checkout_url: null });
  render(<ActivarSuscripcion onVolver={() => undefined} />);
  await waitFor(() => expect(entregarToken).toBeDefined());

  await entregarToken?.("token-produccion");

  await waitFor(() => expect(iniciarMock).toHaveBeenCalledWith(7, "profesional", "token-produccion"));
  expect(screen.queryByLabelText("Card token de diagnóstico")).not.toBeInTheDocument();
});

describe.each([
  [409, /intento de alta pendiente/i],
  [502, /reintentar de forma segura/i],
  [503, /todavía no están configurados/i],
])("errores HTTP", (status, texto) => {
  it(`presenta un mensaje seguro para ${status}`, async () => {
    iniciarMock.mockRejectedValue({ isAxiosError: true, response: { status } });
    render(<ActivarSuscripcion onVolver={() => undefined} />);
    await waitFor(() => expect(entregarToken).toBeDefined());
    await entregarToken?.("token-efimero");
    expect(await screen.findByText(texto)).toBeInTheDocument();
  });
});
