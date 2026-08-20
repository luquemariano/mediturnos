import { expect, it, vi } from "vitest";

import {
  montarFormularioMercadoPago,
  obtenerPublicKeyMercadoPago,
} from "../src/services/mercadoPagoCardForm";

it("inicializa Mercado Pago exclusivamente con la Public Key configurada", async () => {
  vi.stubEnv("VITE_MERCADOPAGO_PUBLIC_KEY", "TEST-public-key-sandbox");
  const constructor = vi.fn(function () {
    return { cardForm: vi.fn(() => ({ getCardFormData: () => ({}) })) };
  });
  window.MercadoPago = constructor as never;

  expect(obtenerPublicKeyMercadoPago()).toBe("TEST-public-key-sandbox");
  await montarFormularioMercadoPago({
    amount: 34_900,
    onToken: vi.fn(),
    onError: vi.fn(),
  });

  expect(constructor).toHaveBeenCalledWith(
    "TEST-public-key-sandbox",
    { locale: "es-AR" },
  );
  const cardForm = constructor.mock.results[0].value.cardForm;
  const config = cardForm.mock.calls[0][0] as { form: Record<string, { id: string }> };
  expect(config.form.submit.id).toBe("form-checkout__submit");
  expect(config.form.identificationType.id).toBe("form-checkout__identificationType");
  expect(config.form.identificationNumber.id).toBe("form-checkout__identificationNumber");
  expect(import.meta.env.MERCADOPAGO_ACCESS_TOKEN).toBeUndefined();
  vi.unstubAllEnvs();
});

it("conserva el flujo normal y sanitiza la identificación en development", async () => {
  vi.stubEnv("VITE_MERCADOPAGO_PUBLIC_KEY", "TEST-public-key-sandbox");
  vi.stubEnv("DEV", true);
  const onToken = vi.fn().mockResolvedValue(undefined);
  const onError = vi.fn();
  const debug = vi.spyOn(console, "debug").mockImplementation(() => undefined);
  const cardFormData = {
    token: "card-token-123",
    paymentMethodId: "visa",
    issuerId: "123",
    installments: 1,
    cardholderEmail: "test@testuser.com",
    identificationType: "DNI",
    identificationNumber: "12345678",
    customField: "preserved",
  };
  const cardForm = {
    getCardFormData: vi.fn(() => cardFormData),
  };
  const constructor = vi.fn(function () {
    return { cardForm: vi.fn(() => cardForm) };
  });
  window.MercadoPago = constructor as never;

  await montarFormularioMercadoPago({ amount: 34_900, onToken, onError });
  const config = constructor.mock.results[0].value.cardForm.mock.calls[0][0] as {
    callbacks: { onSubmit: (event: Event) => Promise<void> };
  };
  const preventDefault = vi.fn();
  await config.callbacks.onSubmit({ preventDefault } as unknown as Event);

  expect(preventDefault).toHaveBeenCalledOnce();
  expect(onToken).toHaveBeenCalledWith("card-token-123");
  expect(onError).not.toHaveBeenCalled();
  expect(debug).toHaveBeenCalledWith("Mercado Pago cardFormData", {
    ...cardFormData,
    token: "[REDACTED]",
    identificationNumber: "***5678",
  });
  expect(cardFormData.identificationNumber).toBe("12345678");

  debug.mockRestore();
  vi.unstubAllEnvs();
});
