import { defineConfig, devices } from "@playwright/test";

const slowMo = Math.max(0, Number.parseInt(process.env.PLAYWRIGHT_SLOW_MO ?? "0", 10) || 0);

export default defineConfig({
  testDir: "./e2e",
  baseURL: "http://127.0.0.1:5174",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30_000,
  expect: { timeout: 5_000 },
  use: {
    ...devices["Desktop Chrome"],
    baseURL: "http://127.0.0.1:5174",
    headless: true,
    navigationTimeout: 15_000,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "off",
    launchOptions: slowMo > 0 ? { slowMo } : undefined,
  },
  reporter: [["line"], ["html", { open: "never" }]],
});
