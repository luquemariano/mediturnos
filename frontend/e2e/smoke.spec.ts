import { test, expect } from "@playwright/test";

test("smoke: frontend y API E2E disponibles", async ({ page, request }) => {
  const api = await request.get("http://127.0.0.1:8001/health/ready");
  expect(api.ok()).toBeTruthy();

  await page.goto("/login");
  await expect(page.getByRole("heading", { name: /iniciar sesión/i })).toBeVisible();
  await expect(page.getByLabel(/correo electrónico|email/i)).toBeVisible();
});
