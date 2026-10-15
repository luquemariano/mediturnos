import { randomUUID } from "node:crypto";
import { test, expect } from "@playwright/test";

const password = "ActividadE2E-segura-123!";

async function completarDatosComunes(page: import("@playwright/test").Page, email: string) {
  await page.getByLabel("Nombre").fill("Prestador");
  await page.getByLabel("Apellido").fill("Sintético");
  await page.getByLabel("Correo electrónico").fill(email);
  await page.getByLabel(/Contraseña/).fill(password);
}

test("registro de estética no solicita ni envía matrícula o especialidad", async ({ page }) => {
  const email = `estetica-${randomUUID()}@example.com`;
  await page.goto("/registro");
  await completarDatosComunes(page, email);
  await page.getByLabel("Actividad profesional").selectOption({ label: "Servicios de estética" });

  await expect(page.getByLabel(/Matrícula/)).toHaveCount(0);
  await expect(page.getByLabel(/Profesión \/ especialidad/)).toHaveCount(0);
  await page.getByRole("button", { name: "Crear cuenta" }).click();

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByText(/Cuenta creada\. Revisá tu correo/)).toBeVisible();
});

test("registro clínico requiere matrícula y especialidad", async ({ page }) => {
  const email = `clinica-${randomUUID()}@example.com`;
  await page.goto("/registro");
  await completarDatosComunes(page, email);
  await page.getByLabel("Actividad profesional").selectOption({ label: "Profesión o actividad con matrícula" });

  const matricula = page.getByLabel(/Matrícula/);
  const especialidad = page.getByLabel(/Profesión \/ especialidad/);
  await expect(matricula).toHaveAttribute("required", "");
  await expect(especialidad).toHaveAttribute("required", "");
  await page.getByRole("button", { name: "Crear cuenta" }).click();
  await expect(page).toHaveURL(/\/registro$/);

  await matricula.fill("E2E-MAT-12345");
  await especialidad.selectOption({ label: "Clínica Médica" });
  await page.getByRole("button", { name: "Crear cuenta" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByText(/Cuenta creada\. Revisá tu correo/)).toBeVisible();
});
