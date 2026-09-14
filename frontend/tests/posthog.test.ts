import { describe, expect, it, vi } from "vitest";
import posthog from "posthog-js";
import { POSTHOG_CONFIG, capturePostHogEvent, isPostHogEnabled } from "../src/posthog";

describe("posthog", () => {
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

  it("no realiza llamadas externas desde el wrapper desactivado", () => {
    const capture = vi.spyOn(posthog, "capture");
    capturePostHogEvent("business_event", { value: "no-send" });
    expect(capture).not.toHaveBeenCalled();
  });
});
