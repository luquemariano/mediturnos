import { describe, expect, it } from "vitest";
import { esRutaPublica, trackEvent, trackPageView } from "../src/analytics";

describe("analytics", () => {
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
});
