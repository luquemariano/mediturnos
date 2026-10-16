import { test, expect } from "@playwright/test";

const apiBase = "http://127.0.0.1:8001";
const clave = process.env.E2E_ADMIN_PASSWORD;
if (!clave) throw new Error("Falta E2E_ADMIN_PASSWORD.");

async function iniciarSesion(page: import("@playwright/test").Page, email: string) {
  await page.goto("/login");
  await page.getByLabel(/correo electrónico|email/i).fill(email);
  await page.getByLabel(/contraseña|password/i).fill(clave!);
  await page.getByRole("button", { name: /iniciar sesión/i }).click();
  await expect(page).toHaveURL(/\/app$/);
}

test("administradora consulta ocupación privada y prepara/envía invitación con proveedor E2E", async ({ page }) => {
  page.on("dialog", (dialog) => dialog.accept());
  await iniciarSesion(page, "profesional.consultorio.e2e@example.com");
  const acceso = page.getByRole("button", { name: /Abrir panel de Consultorio/i });
  await expect(acceso).toBeVisible();
  await acceso.click();
  await expect(page).toHaveURL(/\/app\/consultorio$/);
  await expect(page.getByRole("heading", { name: "Consultorio E2E" })).toBeVisible();
  await expect(page.locator(".notification-center")).toHaveCount(0);

  await page.getByRole("button", { name: "Semana siguiente" }).click();
  const ocupacion = page.locator(".consultorio-admin__bloque").filter({ hasText: "Valentina E2E" });
  await expect(ocupacion).toBeVisible();
  await expect(ocupacion).toContainText("Sala E2E");
  await expect(page.getByText("Paciente Aislamiento E2E")).toHaveCount(0);
  await expect(page.getByText("Dato sintético privado de A")).toHaveCount(0);
  await expect(page.getByText("Laboratorio de control")).toHaveCount(0);
  await page.screenshot({ path: `${process.env.E2E_SCREENSHOTS_DIR ?? "test-results"}/consultorio-admin-desktop.png`, fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  await expect(page.getByRole("heading", { name: "Consultorio E2E" })).toBeVisible();
  await expect(page.getByRole("option", { name: "Sala E2E" })).toHaveCount(1);
  await page.getByRole("button", { name: "Semana siguiente" }).click();
  await expect(page.locator(".consultorio-admin__bloque").filter({ hasText: "Valentina E2E" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.screenshot({ path: `${process.env.E2E_SCREENSHOTS_DIR ?? "test-results"}/consultorio-admin-mobile.png`, fullPage: true });
  await page.setViewportSize({ width: 1280, height: 900 });

  await page.getByRole("button", { name: "Invitaciones" }).click();
  await page.getByLabel("Correo electrónico").fill("invitada.consultorio.e2e@example.com");
  await page.getByLabel("Nombre visible (opcional)").fill("Invitada sintética");
  const fecha = await page.getByLabel("Desde").getAttribute("min");
  await page.getByLabel("Desde").fill(fecha!);
  await page.getByLabel("Día").selectOption("1");
  await page.getByRole("textbox", { name: "Hora", exact: true }).fill("15:00");
  await page.getByRole("button", { name: "Preparar invitación" }).click();
  await expect(page.locator(".consultorio-admin__mensaje")).toContainText("La invitación quedó preparada");

  const fila = page.getByRole("row").filter({ hasText: "invitada.consultorio.e2e@example.com" });
  await expect(fila).toContainText("Preparación");
  await fila.getByRole("button", { name: "Enviar" }).click();
  await expect(page.locator(".consultorio-admin__mensaje")).toContainText("La invitación fue enviada");
  await expect(fila).toContainText("Pendiente");
  await expect(page.locator("body")).not.toContainText(/#token=|token plano/i);
});

test("administradora conserva Consultorio en inicio, agenda, pacientes y disponibilidad", async ({ page }) => {
  await iniciarSesion(page, "profesional.consultorio.e2e@example.com");
  const nav = page.getByRole("navigation", { name: "Navegación profesional" });
  await expect(nav.getByRole("button", { name: "Consultorio" })).toBeVisible();
  await expect(nav.getByRole("button", { name: "Consultorio" })).toBeVisible();
  for (const seccion of ["Inicio", "Mi agenda", "Pacientes", "Mi disponibilidad"]) {
    await nav.getByRole("button", { name: seccion }).click();
    await expect(nav.getByRole("button", { name: "Consultorio" })).toBeVisible();
    await nav.getByRole("button", { name: "Consultorio" }).click();
    await expect(page).toHaveURL(/\/app\/consultorio$/);
    await expect(page.getByRole("heading", { name: "Consultorio E2E" })).toBeVisible();
    await page.getByRole("navigation", { name: "Navegación profesional" }).getByRole("button", { name: "Agenda profesional", exact: true }).click();
    await expect(page).toHaveURL(/\/app$/);
  }
});

test("panel explica el primer conflicto de recurrencia y convierte horas a minutos al guardar", async ({ page }) => {
  await iniciarSesion(page, "profesional.consultorio.e2e@example.com");
  await page.getByRole("button", { name: /Abrir panel de Consultorio/i }).click();
  await expect(page.getByRole("heading", { name: "Consultorio E2E" })).toBeVisible();

  await page.getByRole("button", { name: "Semana siguiente" }).click();
  const lunes = await page.locator(".consultorio-admin__dia time").first().getAttribute("dateTime");
  expect(lunes).toBeTruthy();
  await page.getByRole("button", { name: "Módulos" }).click();
  const formulario = page.locator("form.consultorio-admin__formulario").first();
  const duracion = formulario.getByLabel("Duración (horas)");
  await expect(duracion).toHaveValue("4");
  await expect(formulario.getByLabel("Día")).toHaveValue("0");
  await formulario.getByLabel("Profesional").selectOption({ label: "Valentina E2E" });
  await formulario.getByLabel("Sala").selectOption({ label: "Sala E2E" });
  await formulario.getByLabel("Desde").fill(lunes!);
  await formulario.getByLabel("Hora de inicio").fill("10:00");
  const requests: Array<{ duracion_minutos: number; dia_semana: number }> = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && request.url().includes("/reglas-modulo")) {
      const body = request.postDataJSON();
      requests.push({ duracion_minutos: body.duracion_minutos, dia_semana: body.dia_semana });
    }
  });
  await formulario.getByRole("button", { name: "Crear módulo recurrente" }).click();
  const alerta = page.getByRole("alert");
  await expect(alerta).toContainText("Valentina E2E");
  await expect(alerta).toContainText("09:00 a 13:00");
  await expect(alerta).toContainText("oct");
  expect(requests[0]).toEqual({ duracion_minutos: 240, dia_semana: 0 });

  await duracion.fill("1.5");
  await formulario.getByLabel("Día").selectOption("1");
  await formulario.getByLabel("Hora de inicio").fill("10:00");
  await formulario.getByRole("button", { name: "Crear módulo recurrente" }).click();
  await expect(page.locator(".consultorio-admin__mensaje")).toContainText("La recurrencia quedó configurada");
  expect(requests[1]).toEqual({ duracion_minutos: 90, dia_semana: 1 });
  await expect(page.getByText(/10:00 · 1,5 horas/)).toBeVisible();
});

test("profesional no administradora no ve el acceso y la ruta protegida no revela el consultorio", async ({ page }) => {
  await iniciarSesion(page, "profesional.isolation.e2e@example.com");
  await expect(page.getByRole("button", { name: /Abrir panel de Consultorio/i })).toHaveCount(0);
  await page.goto("/app/consultorio");
  await expect(page.getByRole("heading", { name: "Consultorio no disponible" })).toBeVisible();
  await expect(page.getByText("Consultorio E2E")).toHaveCount(0);

  const login = await page.request.post(`${apiBase}/auth/login`, { data: { email: "profesional.isolation.e2e@example.com", password: clave } });
  expect(login.ok()).toBeTruthy();
  const accessToken = (await login.json()).access_token as string;
  const list = await page.request.get(`${apiBase}/consultorios`, { headers: { Authorization: `Bearer ${accessToken}` } });
  expect(list.ok()).toBeTruthy();
  expect(await list.json()).toEqual([]);
});

test("módulo con turno bloquea suspensión con sólo el conteo y un módulo libre admite cambios", async ({ page }) => {
  page.on("dialog", (dialog) => dialog.accept());
  await iniciarSesion(page, "profesional.consultorio.e2e@example.com");
  await page.getByRole("button", { name: /Abrir panel de Consultorio/i }).click();
  await page.getByRole("button", { name: "Semana siguiente" }).click();
  await page.getByRole("button", { name: "Módulos" }).click();
  const lista = page.locator(".consultorio-admin__lista-reglas li");
  const ocupado = lista.filter({ hasText: "09:00–13:00" }).first();
  await ocupado.getByRole("button", { name: "Suspender" }).click();
  const alerta = page.getByRole("alert");
  await expect(alerta).toHaveText("El cambio está bloqueado porque afecta a 1 turno. No se modificó ningún turno.");
  await expect(alerta).not.toContainText(/Paciente|E2E|clínic/i);

  const token = await page.evaluate(() => localStorage.getItem("access_token"));
  expect(token).toBeTruthy();
  const headers = { Authorization: `Bearer ${token}` };
  const consultorios = await page.request.get(`${apiBase}/consultorios`, { headers });
  expect(consultorios.ok()).toBeTruthy();
  const consultorioId = (await consultorios.json())[0].id as number;
  const ahora = new Date();
  const desde = ahora.toISOString();
  const hasta = new Date(ahora.getTime() + 80 * 86400000).toISOString();
  const respuestaModulos = await page.request.get(`${apiBase}/consultorios/${consultorioId}/modulos`, { headers, params: { desde, hasta } });
  expect(respuestaModulos.ok()).toBeTruthy();
  const modulos = await respuestaModulos.json() as Array<{ id: number; estado: string; fecha_inicio: string; fecha_fin: string; profesional_id: number | null }>;
  const lunesesLibres = modulos.filter((item) => item.estado === "activa" && item.profesional_id !== null && new Date(item.fecha_inicio).getUTCDay() === 1 && new Date(item.fecha_inicio) > ahora).sort((a, b) => a.fecha_inicio.localeCompare(b.fecha_inicio));
  expect(lunesesLibres.length).toBeGreaterThan(1);
  const libre = lunesesLibres[lunesesLibres.length - 1];
  const nuevoInicio = new Date(new Date(libre.fecha_inicio).getTime() - 60 * 60 * 1000);
  const nuevoFin = new Date(new Date(libre.fecha_fin).getTime() - 60 * 60 * 1000);
  const cambio = await page.request.patch(`${apiBase}/consultorios/${consultorioId}/modulos/${libre.id}`, { headers, data: { fecha_inicio: nuevoInicio.toISOString(), fecha_fin: nuevoFin.toISOString() } });
  expect(cambio.status()).toBe(200);
  expect((await cambio.json()).estado).toBe("activa");
});
