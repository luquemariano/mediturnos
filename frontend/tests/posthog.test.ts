import { beforeEach, describe, expect, it, vi } from "vitest";
import posthog from "posthog-js";
import { POSTHOG_CONFIG, capturePostHogEvent, isPostHogEnabled } from "../src/posthog";

describe("posthog", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
  });

  it("queda desactivado sin configuración productiva", () => {
    expect(isPostHogEnabled()).toBe(false);
    expect(() => capturePostHogEvent("business_event")).not.toThrow();
  });

  it("expone configuración de privacidad estricta y autocapture apagado", () => {
    expect(POSTHOG_CONFIG.autocapture).toBe(false);
    expect(POSTHOG_CONFIG.mask_all_text).toBe(true);
    expect(POSTHOG_CONFIG.mask_all_element_attributes).toBe(true);
    expect(POSTHOG_CONFIG.session_recording).toMatchObject({
      maskAllInputs: true,
      maskAllElementAttributes: true,
      maskTextSelector: "*",
    });
  });

  it("envía sólo un evento permitido y propiedades primitivas permitidas", () => {
    vi.stubEnv("PROD", "true");
    vi.stubEnv("VITE_POSTHOG_PROJECT_TOKEN", "test-token");
    vi.stubEnv("VITE_POSTHOG_HOST", "https://eu.i.posthog.com");
    const capture = vi.spyOn(posthog, "capture");
    capturePostHogEvent("patient_created", { source: "patients", email: "x@y.test", patient_id: "1", nombre: "Ana", observaciones: "texto", extra: ["x"] as never });
    capturePostHogEvent("not_allowed", { source: "test" });
    expect(capture).toHaveBeenCalledWith("patient_created", { source: "patients" });
    expect(capture).not.toHaveBeenCalledWith("not_allowed", expect.anything());
  });

  it("permite el clic a ayuda con sólo un source seguro", () => {
    vi.stubEnv("PROD", "true");
    vi.stubEnv("VITE_POSTHOG_PROJECT_TOKEN", "test-token");
    vi.stubEnv("VITE_POSTHOG_HOST", "https://eu.i.posthog.com");
    const capture = vi.spyOn(posthog, "capture");
    capturePostHogEvent("help_article_click", { source: "landing_recordatorios", email: "no-enviar@example.com" });
    expect(capture).toHaveBeenCalledWith("help_article_click", { source: "landing_recordatorios" });
  });

  it.each(["public_booking_attempt", "public_booking_success"])("envía %s exactamente al posthog real", (eventName) => {
    vi.stubEnv("PROD", "true");
    vi.stubEnv("VITE_POSTHOG_PROJECT_TOKEN", "test-token");
    vi.stubEnv("VITE_POSTHOG_HOST", "https://eu.i.posthog.com");
    const capture = vi.spyOn(posthog, "capture");

    capturePostHogEvent(eventName, { source: "public_booking" });

    expect(capture).toHaveBeenCalledTimes(1);
    expect(capture).toHaveBeenCalledWith(eventName, { source: "public_booking" });
  });

  it("filtra propiedades no permitidas y descarta eventos fuera del allowlist", () => {
    vi.stubEnv("PROD", "true");
    vi.stubEnv("VITE_POSTHOG_PROJECT_TOKEN", "test-token");
    vi.stubEnv("VITE_POSTHOG_HOST", "https://eu.i.posthog.com");
    const capture = vi.spyOn(posthog, "capture");

    capturePostHogEvent("public_booking_success", {
      source: "public_booking",
      email: "no-enviar@example.com",
      booking_id: "no-enviar",
    });
    capturePostHogEvent("not_allowed", { source: "test" });

    expect(capture).toHaveBeenCalledTimes(1);
    expect(capture).toHaveBeenCalledWith("public_booking_success", { source: "public_booking" });
    expect(capture).not.toHaveBeenCalledWith("not_allowed", expect.anything());
  });

  it("no realiza llamadas externas desde el wrapper desactivado", () => {
    vi.stubEnv("PROD", "false");
    const capture = vi.spyOn(posthog, "capture");
    capture.mockClear();
    capturePostHogEvent("business_event", { value: "no-send" });
    expect(capture).not.toHaveBeenCalled();
  });
});
