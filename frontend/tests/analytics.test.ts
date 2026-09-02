import { afterEach, describe, expect, it, vi } from "vitest";
import { esRutaPublica, trackEvent, trackPageView } from "../src/analytics";

describe("analytics", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    delete window.gtag;
    window.dataLayer = [];
  });

  it("no lanza errores si GA4 no está disponible", () => {
    expect(() => trackEvent("sign_up_click", { source: "landing" })).not.toThrow();
    expect(() => trackPageView("/")).not.toThrow();
  });

  it("excluye rutas privadas y URLs con parámetros", () => {
    expect(esRutaPublica("/app/pacientes")).toBe(false);
    expect(esRutaPublica("/suscripcion/retorno")).toBe(false);
    expect(esRutaPublica("/ayuda/agenda")).toBe(true);
    expect(() => trackPageView("/app/pacientes?paciente_id=42#evolucion")).not.toThrow();
  });

  it("filtra parámetros a campos comerciales permitidos", () => {
    expect(() => trackEvent("subscription_start", { plan: "profesional", email: "persona@example.com", paciente_id: "42" })).not.toThrow();
  });

  it("usa la estructura arguments del snippet oficial y conserva la configuración", () => {
    vi.stubEnv("PROD", true);
    trackEvent("sign_up_click", { source: "landing" });
    const entradas = window.dataLayer as IArguments[][];
    expect(entradas).toHaveLength(2);
    expect(Array.from(entradas[0])).toEqual(["js", expect.any(Date)]);
    expect(Array.from(entradas[1])).toEqual(["config", "G-7Y07NRSBZE", { send_page_view: false }]);
  });
});
