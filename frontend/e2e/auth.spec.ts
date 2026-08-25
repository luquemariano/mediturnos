import { test, expect } from "@playwright/test";

const email = process.env.E2E_ADMIN_EMAIL ?? "admin.e2e@example.com";
const password = process.env.E2E_ADMIN_PASSWORD;

if (!password) throw new Error("Falta E2E_ADMIN_PASSWORD.");

test("administrador puede iniciar y cerrar sesión", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel(/correo electrónico|email/i).fill(email);
  await page.getByLabel(/contraseña|password/i).fill(password);
  await page.getByRole("button", { name: /iniciar sesión/i }).click();

  await expect(page).toHaveURL(/\/app$/);
  await expect(page.getByRole("button", { name: /cerrar sesión/i })).toBeVisible();

  await page.getByRole("button", { name: /cerrar sesión/i }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("heading", { name: /iniciar sesión/i })).toBeVisible();
});
