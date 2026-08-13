import assert from "node:assert/strict";
import { test } from "vitest";

import {
  claveFechaNegocio,
  etiquetaFechaProximoTurno,
  fechaActualNegocio,
  formatearHoraTurno,
} from "../src/utils/fechaTurno.ts";

test("agrupa en el día de Buenos Aires cerca de medianoche UTC", () => {
  assert.equal(
    claveFechaNegocio("2026-08-16T02:30:00Z"),
    "2026-08-15",
  );
  assert.equal(
    formatearHoraTurno("2026-08-16T02:30:00Z"),
    "23:30",
  );
});

test("etiqueta la fecha contextual del próximo turno", () => {
  const ahora = new Date("2026-08-13T15:00:00Z");
  assert.equal(etiquetaFechaProximoTurno("2026-08-13T18:00:00Z", ahora), "HOY");
  assert.equal(etiquetaFechaProximoTurno("2026-08-14T13:30:00Z", ahora), "MAÑANA");
  assert.equal(etiquetaFechaProximoTurno("2026-08-17T13:30:00Z", ahora), "LUNES 17");
  assert.equal(etiquetaFechaProximoTurno("2026-08-27T13:30:00Z", ahora), "27 AGO");
});

test("determina hoy respetando el cambio de día en Buenos Aires", () => {
  const ahora = new Date("2026-08-14T01:30:00Z");
  assert.equal(etiquetaFechaProximoTurno("2026-08-14T02:30:00Z", ahora), "HOY");
  assert.equal(etiquetaFechaProximoTurno("2026-08-14T03:30:00Z", ahora), "MAÑANA");
});

test("calcula hoy según Buenos Aires y no según UTC", () => {
  assert.equal(
    fechaActualNegocio(new Date("2026-08-16T01:00:00Z")),
    "2026-08-15",
  );
});
