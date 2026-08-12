import assert from "node:assert/strict";
import { test } from "vitest";

import {
  claveFechaNegocio,
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

test("calcula hoy según Buenos Aires y no según UTC", () => {
  assert.equal(
    fechaActualNegocio(new Date("2026-08-16T01:00:00Z")),
    "2026-08-15",
  );
});
