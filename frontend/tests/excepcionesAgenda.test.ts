import { describe, expect, it } from "vitest";
import { etiquetaExcepcion, mapaExcepciones } from "../src/utils/excepcionesAgenda";
import type { DisponibilidadExcepcion } from "../src/types/disponibilidad";

const excepcion = (fecha: string, origen: DisponibilidadExcepcion["origen"], tipo: DisponibilidadExcepcion["tipo"] = "cierre_dia"): DisponibilidadExcepcion => ({ id: Number(fecha.slice(-2)), profesional_id: 1, fecha, tipo, origen, nombre: null, hora_inicio: null, hora_fin: null, activa: true });

describe("excepciones visuales de agenda", () => {
  it("identifica feriado, cerrado y vacaciones desde el contrato existente", () => {
    const mapa = mapaExcepciones([excepcion("2026-08-20", "feriado"), excepcion("2026-08-21", "manual"), excepcion("2026-08-22", "vacaciones")]);
    expect(mapa.get("2026-08-20")).toBe("feriado"); expect(mapa.get("2026-08-21")).toBe("cerrado"); expect(mapa.get("2026-08-22")).toBe("vacaciones");
  });

  it("resuelve prioridad vacaciones sobre cerrado y feriado", () => {
    const mapa = mapaExcepciones([excepcion("2026-08-20", "feriado"), excepcion("2026-08-20", "manual"), excepcion("2026-08-20", "vacaciones")]);
    expect(mapa.get("2026-08-20")).toBe("vacaciones"); expect(etiquetaExcepcion(mapa.get("2026-08-20"))).toBe("Vacaciones");
  });

  it("ignora excepciones inactivas", () => {
    const inactiva = { ...excepcion("2026-08-20", "feriado"), activa: false };
    expect(mapaExcepciones([inactiva])).toEqual(new Map());
  });

  it("marca cada fecha recibida para un rango de vacaciones", () => {
    const mapa = mapaExcepciones(["14", "15", "16"].map((dia) => excepcion(`2026-09-${dia}`, "vacaciones")));
    expect([...mapa.keys()]).toEqual(["2026-09-14", "2026-09-15", "2026-09-16"]);
  });
});
