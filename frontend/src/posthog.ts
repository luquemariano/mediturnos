import posthog from "posthog-js";
import type { PostHogConfig, Properties } from "posthog-js";

let initialized = false;
export const POSTHOG_ALLOWED_EVENTS = new Set([
  "sign_up_complete", "email_verified", "login_success", "onboarding_completed",
  "prestation_created", "availability_created", "patient_created", "appointment_created",
  "appointment_updated", "appointment_cancelled", "public_booking_view",
  "public_booking_availability_view", "public_booking_attempt", "public_booking_success",
  "public_booking_error", "public_booking_cancel", "public_booking_reschedule", "help_article_click",
]);
const ALLOWED_PROPERTIES = new Set(["source", "role", "plan", "resultado", "error_type", "modalidad", "duracion"]);
const ERROR_TYPES = new Set(["validation", "conflict", "rate_limit", "network", "server", "unknown"]);
const DIAGNOSTIC_EVENTS = new Set(["patient_created", "appointment_created", "email_verified"]);
export function normalizePostHogError(error: unknown): string {
  const status = typeof error === "object" && error !== null && "response" in error ? (error as { response?: { status?: number } }).response?.status : undefined;
  if (status === 409) return "conflict";
  if (status === 429) return "rate_limit";
  if (typeof status === "number" && status >= 500) return "server";
  if (typeof status === "number" && status >= 400) return "validation";
  if (typeof error === "object" && error !== null && "request" in error) return "network";
  return "unknown";
}

export const POSTHOG_CONFIG: Partial<PostHogConfig> = {
  api_host: import.meta.env.VITE_POSTHOG_HOST?.trim(),
  autocapture: false,
  capture_pageview: true,
  capture_pageleave: true,
  mask_all_text: true,
  mask_all_element_attributes: true,
  session_recording: {
    maskAllInputs: true,
    maskAllElementAttributes: true,
    maskTextSelector: "*",
    blockSelector: "input, textarea, select, [contenteditable='true']",
  },
};

export function isPostHogEnabled(): boolean {
  return Boolean(import.meta.env.PROD && import.meta.env.VITE_POSTHOG_PROJECT_TOKEN?.trim() && import.meta.env.VITE_POSTHOG_HOST?.trim());
}

export function initializePostHog(): typeof posthog {
  if (isPostHogEnabled() && !initialized) {
    posthog.init(import.meta.env.VITE_POSTHOG_PROJECT_TOKEN!.trim(), { ...POSTHOG_CONFIG, api_host: import.meta.env.VITE_POSTHOG_HOST!.trim() });
    initialized = true;
  }
  return posthog;
}

export function posthogParaRuta(pathname: string): typeof posthog {
  if (pathname === "/baja-novedades") return posthog;
  return initializePostHog();
}

export function capturePostHogEvent(name: string, properties?: Properties): void {
  if (window.location.pathname === "/baja-novedades" || !isPostHogEnabled() || !POSTHOG_ALLOWED_EVENTS.has(name)) return;
  const safeProperties = Object.fromEntries(Object.entries(properties ?? {}).filter(([key, value]) => {
    if (!ALLOWED_PROPERTIES.has(key) || typeof value !== "string") return false;
    return key !== "error_type" || ERROR_TYPES.has(value);
  }));
  if (import.meta.env.PROD && DIAGNOSTIC_EVENTS.has(name)) {
    console.debug("[posthog-diagnostic]", {
      event: name,
      properties: Object.fromEntries(
        Object.entries(safeProperties).filter(([key]) =>
          key === "source" || key === "role"
        )
      ),
    });
  }
  posthog.capture(name, safeProperties);
}

export { posthog };
