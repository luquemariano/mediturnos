type CardFormData = { token?: string; [key: string]: unknown };
type CardForm = {
  getCardFormData: () => CardFormData;
  unmount?: () => void;
};
type MercadoPagoInstance = {
  cardForm: (config: Record<string, unknown>) => CardForm;
};
type MercadoPagoConstructor = new (
  publicKey: string,
  options: { locale: string },
) => MercadoPagoInstance;

function sanitizarCardFormData(cardFormData: CardFormData): CardFormData {
  const copia = { ...cardFormData };
  if (copia.token !== undefined) copia.token = "[REDACTED]";
  const identificationNumber = copia.identificationNumber;
  if (identificationNumber !== undefined && identificationNumber !== null) {
    const valor = String(identificationNumber);
    copia.identificationNumber = `***${valor.slice(-4)}`;
  }
  return copia;
}

declare global {
  interface Window {
    MercadoPago?: MercadoPagoConstructor;
  }
}

let cargaSdk: Promise<void> | null = null;

function registrarErrorDeMontaje(error: unknown): void {
  if (!import.meta.env.DEV) return;
  const tipo = error instanceof Error ? error.name : "UnknownError";
  const detalle = error instanceof Error
    ? error.message
      .replace(/Bearer\s+\S+/gi, "Bearer [REDACTED]")
      .replace(/\b\d{12,19}\b/g, "[REDACTED]")
      .slice(0, 240)
    : "No se pudo inicializar el formulario.";
  console.warn("Mercado Pago cardForm no pudo inicializarse", { tipo, detalle });
}

export function obtenerPublicKeyMercadoPago(): string {
  const key = import.meta.env.VITE_MERCADOPAGO_PUBLIC_KEY?.trim();
  if (!key) throw new Error("Mercado Pago no está configurado.");
  return key;
}

async function cargarSdkMercadoPago(): Promise<void> {
  if (window.MercadoPago) return;
  cargaSdk ??= new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://sdk.mercadopago.com/js/v2";
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("No se pudo cargar Mercado Pago."));
    document.head.appendChild(script);
  });
  await cargaSdk;
  if (!window.MercadoPago) throw new Error("Mercado Pago no quedó disponible.");
}

export async function montarFormularioMercadoPago({
  amount,
  onToken,
  onError,
}: {
  amount: number;
  onToken: (token: string) => Promise<void>;
  onError: () => void;
}): Promise<() => void> {
  await cargarSdkMercadoPago();
  const MercadoPago = window.MercadoPago;
  if (!MercadoPago) throw new Error("Mercado Pago no quedó disponible.");
  const mp = new MercadoPago(obtenerPublicKeyMercadoPago(), { locale: "es-AR" });
  let cardForm: CardForm;
  try {
    cardForm = mp.cardForm({
      amount: String(amount),
      iframe: true,
      form: {
        id: "form-checkout",
        cardNumber: { id: "form-checkout__cardNumber" },
        expirationDate: { id: "form-checkout__expirationDate" },
        securityCode: { id: "form-checkout__securityCode" },
        cardholderName: { id: "form-checkout__cardholderName" },
        issuer: { id: "form-checkout__issuer" },
        installments: { id: "form-checkout__installments" },
        identificationType: { id: "form-checkout__identificationType" },
        identificationNumber: { id: "form-checkout__identificationNumber" },
        cardholderEmail: { id: "form-checkout__cardholderEmail" },
        submit: { id: "form-checkout__submit" },
      },
      callbacks: {
        onFormMounted: (error?: unknown) => {
          if (error) registrarErrorDeMontaje(error);
        },
        onSubmit: async (event: Event) => {
          event.preventDefault();
          const cardFormData = cardForm.getCardFormData();
          const token = cardFormData.token;
          if (!token) return onError();
          if (import.meta.env.DEV) {
            console.debug("Mercado Pago cardFormData", sanitizarCardFormData(cardFormData));
          }
          await onToken(token);
        },
        onError,
      },
    });
  } catch (error) {
    registrarErrorDeMontaje(error);
    throw error;
  }
  return () => cardForm.unmount?.();
}
