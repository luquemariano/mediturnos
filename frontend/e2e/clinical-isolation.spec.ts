import { test, expect } from "@playwright/test";
import type { APIRequestContext } from "@playwright/test";

const apiBase = "http://127.0.0.1:8001";
const password = process.env.E2E_ADMIN_PASSWORD;
if (!password) throw new Error("Falta E2E_ADMIN_PASSWORD.");

async function tokenFor(request: APIRequestContext, email: string) {
  const response = await request.post(`${apiBase}/auth/login`, { data: { email, password } });
  expect(response.ok()).toBeTruthy();
  return (await response.json()).access_token as string;
}

async function patientIdFor(request: APIRequestContext, adminToken: string) {
  const response = await request.get(`${apiBase}/pacientes/`, { headers: { Authorization: `Bearer ${adminToken}` } });
  expect(response.ok()).toBeTruthy();
  const patients = await response.json();
  const patient = patients.find((entry) => entry.email === "consultorio.isolation.e2e@example.com");
  expect(patient).toBeTruthy();
  return patient.id as number;
}

test("dos profesionales que comparten paciente sólo leen su contenido clínico", async ({ request }) => {
  const tokenA = await tokenFor(request, "profesional.screenshots@example.com");
  const tokenB = await tokenFor(request, "profesional.isolation.e2e@example.com");
  const adminToken = await tokenFor(request, process.env.E2E_ADMIN_EMAIL ?? "admin.e2e@example.com");
  const patientId = await patientIdFor(request, adminToken);
  for (const token of [tokenA, tokenB]) {
    const patients = await request.get(`${apiBase}/profesionales/me/pacientes`, { headers: { Authorization: `Bearer ${token}` } });
    expect((await patients.json()).map((entry) => entry.id)).toContain(patientId);
  }

  const profileA = await request.get(`${apiBase}/pacientes/${patientId}/clinical-profile`, { headers: { Authorization: `Bearer ${tokenA}` } });
  const profileB = await request.get(`${apiBase}/pacientes/${patientId}/clinical-profile`, { headers: { Authorization: `Bearer ${tokenB}` } });
  expect(profileA.ok()).toBeTruthy();
  expect(profileB.ok()).toBeTruthy();
  expect((await profileA.json()).antecedentes).toBe("Dato sintético privado de A");
  expect((await profileB.json()).antecedentes).toBe("Dato sintético privado de B");

  const evolutionsA = await request.get(`${apiBase}/pacientes/${patientId}/evoluciones`, { headers: { Authorization: `Bearer ${tokenA}` } });
  const evolutionsB = await request.get(`${apiBase}/pacientes/${patientId}/evoluciones`, { headers: { Authorization: `Bearer ${tokenB}` } });
  expect(evolutionsA.ok()).toBeTruthy();
  expect(evolutionsB.ok()).toBeTruthy();
  const bodyA = await evolutionsA.json();
  const bodyB = await evolutionsB.json();
  expect(bodyA.map((entry) => entry.contenido)).toContain("Evolución sintética privada A");
  expect(bodyA.map((entry) => entry.contenido)).not.toContain("Evolución sintética privada B");
  expect(bodyB.map((entry) => entry.contenido)).toContain("Evolución sintética privada B");
  expect(bodyB.map((entry) => entry.contenido)).not.toContain("Evolución sintética privada A");

  const requestsA = await request.get(`${apiBase}/pacientes/${patientId}/study-requests`, { headers: { Authorization: `Bearer ${tokenA}` } });
  const requestsB = await request.get(`${apiBase}/pacientes/${patientId}/study-requests`, { headers: { Authorization: `Bearer ${tokenB}` } });
  expect((await requestsA.json()).map((entry) => entry.title)).toContain("Solicitud sintética privada A");
  expect((await requestsA.json()).map((entry) => entry.title)).not.toContain("Solicitud sintética privada B");
  expect((await requestsB.json()).map((entry) => entry.title)).toContain("Solicitud sintética privada B");
  expect((await requestsB.json()).map((entry) => entry.title)).not.toContain("Solicitud sintética privada A");

  const documentsA = await request.get(`${apiBase}/pacientes/${patientId}/documents`, { headers: { Authorization: `Bearer ${tokenA}` } });
  const documentsB = await request.get(`${apiBase}/pacientes/${patientId}/documents`, { headers: { Authorization: `Bearer ${tokenB}` } });
  expect((await documentsA.json()).map((entry) => entry.original_filename)).toContain("sintetico-privado.pdf");
  expect(await documentsB.json()).toEqual([]);
});
