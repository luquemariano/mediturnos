import { test, expect } from "@playwright/test";

test("administrador accede a la vista protegida de cuentas", async ({ page }) => {
  const password = process.env.E2E_ADMIN_PASSWORD;
  if (!password) throw new Error("Falta E2E_ADMIN_PASSWORD.");
  await page.goto("/login");
  await page.getByLabel(/correo electrónico|email/i).fill(process.env.E2E_ADMIN_EMAIL ?? "admin.e2e@example.com");
  await page.getByLabel(/contraseña|password/i).fill(password);
  await page.getByRole("button", { name: /iniciar sesión/i }).click();
  await expect(page).toHaveURL(/\/app$/);

  await page.getByRole("button", { name: /cuentas/i }).click();
  await expect(page.getByRole("heading", { name: "Cuentas" })).toBeVisible();
  await expect(page.getByText("Administración comercial")).toBeVisible();
});
