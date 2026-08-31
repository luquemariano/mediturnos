import { test, expect } from "@playwright/test";

test.describe("Centro de Ayuda público", () => {
  test("carga portada, artículo, navegación e 404 sin login", async ({ page }) => {
    await page.goto("/ayuda");
    await expect(page.getByRole("heading", { name: "Centro de Ayuda" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Primeros pasos" })).toBeVisible();
    for (const title of ["Prestaciones", "Disponibilidad", "Agenda", "Turnos", "Pacientes", "Historia clínica", "Documentos", "Estudios", "Recordatorios", "Suscripción"]) await expect(page.getByRole("heading", { name: title, exact: true })).toBeVisible();
    await page.getByRole("button", { name: /Ver guía/ }).first().click();
    await expect(page).toHaveURL(/\/ayuda\/primeros-pasos$/);
    await expect(page.getByRole("heading", { name: "Primeros pasos" })).toBeVisible();
    await page.goBack();
    await expect(page).toHaveURL(/\/ayuda$/);
    await page.goto("/ayuda/no-existe");
    await expect(page.getByRole("heading", { name: "No encontramos esta guía" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Volver al Centro de Ayuda" })).toBeVisible();
  });

  test("se adapta al viewport mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/ayuda/primeros-pasos");
    await expect(page.getByRole("heading", { name: "Primeros pasos" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "3. Crear una prestación" })).toBeVisible();
    await page.goto("/ayuda/prestaciones");
    await expect(page.getByRole("heading", { name: "Crear una prestación", exact: true })).toBeVisible();
    await page.goto("/ayuda/disponibilidad");
    await expect(page.getByRole("heading", { name: "Varias franjas en un mismo día", exact: true })).toBeVisible();
    await page.goto("/ayuda/agenda");
    await expect(page.getByRole("heading", { name: "Vista Día", exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Vista Semana", exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Vista Mes", exact: true })).toBeVisible();
    await page.goto("/ayuda/turnos");
    await expect(page.getByRole("heading", { name: "Crear un turno", exact: true })).toBeVisible();
    await page.goto("/ayuda/pacientes");
    await expect(page.getByRole("heading", { name: "Crear un paciente", exact: true })).toBeVisible();
    await page.goto("/ayuda/historia-clinica");
    await expect(page.getByRole("heading", { name: "Resumen clínico", exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Agregar una evolución", exact: true })).toBeVisible();
    await page.goto("/ayuda/documentos");
    await expect(page.getByRole("heading", { name: "Formatos admitidos", exact: true })).toBeVisible();
    await page.goto("/ayuda/estudios");
    await expect(page.getByRole("heading", { name: "Crear una solicitud", exact: true })).toBeVisible();
    await page.goto("/ayuda/recordatorios");
    await expect(page.getByRole("heading", { name: "Qué son los recordatorios", exact: true })).toBeVisible();
    await page.goto("/ayuda/suscripcion");
    await expect(page.getByRole("heading", { name: "Qué es la suscripción de Turnelia", exact: true })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  });

  test("abre una imagen de ayuda en lightbox y permite cerrarla", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/ayuda/agenda");
    const image = page.getByRole("button", { name: /Ampliar imagen:/ }).first();
    await expect(image).toBeVisible();
    await image.click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page.getByRole("dialog").getByRole("img")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog")).toBeHidden();
  });
});
