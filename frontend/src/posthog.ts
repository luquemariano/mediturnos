import posthog from "posthog-js";
import type { PostHogConfig, Properties } from "posthog-js";

const projectToken = import.meta.env.VITE_POSTHOG_PROJECT_TOKEN?.trim();
const host = import.meta.env.VITE_POSTHOG_HOST?.trim();
let initialized = false;
const ALLOWED_EVENTS = new Set<string>();

export const POSTHOG_CONFIG: Partial<PostHogConfig> = {
  api_host: host,
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
  return Boolean(import.meta.env.PROD && projectToken && host);
}

export function initializePostHog(): typeof posthog {
  if (isPostHogEnabled() && !initialized) {
    posthog.init(projectToken!, POSTHOG_CONFIG);
    initialized = true;
  }
  return posthog;
}

export function capturePostHogEvent(name: string, properties?: Properties): void {
  if (!isPostHogEnabled() || !ALLOWED_EVENTS.has(name)) return;
  posthog.capture(name, properties);
}

export { posthog };
