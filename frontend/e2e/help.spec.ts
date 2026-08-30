import { test, expect } from "@playwright/test";

test.describe("Centro de Ayuda público", () => {
  test("carga portada, artículo, navegación e 404 sin login", async ({ page }) => {
    await page.goto("/ayuda");
    await expect(page.getByRole("heading", { name: "Centro de Ayuda" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Primeros pasos" })).toBeVisible();
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
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  });
});
