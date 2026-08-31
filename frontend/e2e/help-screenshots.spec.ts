import { test, expect, type Page } from "@playwright/test";

const OUT = "../public/help/screenshots";
const password = process.env.E2E_ADMIN_PASSWORD;
if (!password) throw new Error("Falta E2E_ADMIN_PASSWORD.");

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel(/correo electrónico|email/i).fill("profesional.screenshots@example.com");
  await page.getByLabel(/contraseña|password/i).fill(password!);
  await page.getByRole("button", { name: /iniciar sesión/i }).click();
  await expect(page.getByRole("heading", { name: /panel|buen/i }).first()).toBeVisible({ timeout: 15_000 });
}

async function shot(page: Page, name: string) {
  await page.waitForLoadState("networkidle");
  await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true });
}

test("genera las capturas documentales S01–S17 con datos E2E ficticios", async ({ page }) => {
  await login(page);
  await page.goto("/onboarding/perfil");
  await expect(page.getByRole("heading", { name: "Revisá tu perfil" })).toBeVisible();
  await shot(page, "01-onboarding-perfil");
  await page.getByRole("button", { name: "Continuar" }).click();
  await expect(page.getByRole("heading", { name: "Configurá tus prestaciones" })).toBeVisible();
  await shot(page, "02-prestacion-crear");
  await page.getByRole("button", { name: "Continuar" }).click();
  await expect(page.getByRole("heading", { name: "Configurá tus horarios de atención" })).toBeVisible();
  await shot(page, "03-disponibilidad-semanal");
  await page.getByRole("button", { name: "Continuar" }).click();
  await expect(page.getByRole("heading", { name: "Tu cuenta está lista" })).toBeVisible();
  await page.getByRole("button", { name: "Ir a mi panel" }).click();
  await expect(page.getByRole("heading", { name: /Buen día|Buenas tardes|Buenas noches/ })).toBeVisible();

  const nav = page.getByRole("navigation", { name: "Navegación profesional" });
  await nav.getByRole("button", { name: "Mi disponibilidad" }).click();
  await expect(page.getByRole("heading", { name: "Mi disponibilidad" })).toBeVisible();
  await shot(page, "04-disponibilidad-excepciones");
  await nav.getByRole("button", { name: "Mi agenda" }).click();
  await expect(page.getByRole("heading", { name: "Mi agenda" })).toBeVisible();
  await shot(page, "05-agenda-dia");
  await page.getByRole("button", { name: "Semana" }).click(); await shot(page, "06-agenda-semana");
  await page.getByRole("button", { name: "Mes" }).click(); await shot(page, "07-agenda-mes");
  await page.getByRole("button", { name: "Día" }).click();
  await page.getByRole("button", { name: /Nuevo turno/i }).click(); await expect(page.getByRole("heading", { name: "Nuevo turno" })).toBeVisible(); await shot(page, "08-turno-nuevo");
  await page.getByRole("button", { name: /Cerrar/i }).click();
  await page.getByRole("button", { name: /Reprogramar/i }).first().click(); await expect(page.getByRole("heading", { name: "Reprogramar turno" })).toBeVisible(); await shot(page, "09-turno-reprogramar");
  await page.getByRole("button", { name: /Cerrar/i }).click();
  await nav.getByRole("button", { name: "Pacientes" }).click(); await expect(page.getByRole("heading", { name: "Pacientes" })).toBeVisible(); await shot(page, "10-pacientes-listado");
  await page.getByRole("button", { name: "Ver paciente" }).first().click(); await expect(page.getByRole("heading", { name: "Historial de turnos" })).toBeVisible(); await shot(page, "11-paciente-detalle");
  await page.getByRole("heading", { name: "Resumen clínico" }).scrollIntoViewIfNeeded(); await shot(page, "12-resumen-clinico");
  await page.getByRole("button", { name: "Nueva evolución" }).click(); await shot(page, "13-evolucion-clinica");
  await page.getByRole("heading", { name: "Documentos" }).scrollIntoViewIfNeeded(); await shot(page, "14-documentos");
  await page.getByRole("heading", { name: "Estudios solicitados" }).scrollIntoViewIfNeeded(); await shot(page, "15-estudio-solicitud");
  await page.getByRole("button", { name: "Revisar" }).first().click(); await expect(page.getByRole("heading", { name: "Documentos recibidos" })).toBeVisible(); await shot(page, "17-estudio-revision");
  await page.goto("/estudios/enviar"); await shot(page, "16-estudio-carga-publica");
});
