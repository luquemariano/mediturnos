import { describe, expect, it } from "vitest";
import { distribuirSolapamientos, diasSemana, finSemana, inicioSemana, semanaAnterior, semanaSiguiente } from "../src/utils/calendario";

describe("utilidades de vista semanal", () => {
  it("calcula lunes a domingo y navegación semanal", () => {
    expect(diasSemana("2026-09-02")).toEqual(["2026-08-31", "2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-05", "2026-09-06"]);
    expect(inicioSemana("2026-09-02")).toBe("2026-08-31");
    expect(finSemana("2026-09-02")).toBe("2026-09-06");
    expect(semanaAnterior("2026-09-02")).toBe("2026-08-24");
    expect(semanaSiguiente("2026-09-02")).toBe("2026-09-07");
  });

  it("distribuye intervalos solapados y deja contiguos en la misma columna", () => {
    const resultado = distribuirSolapamientos([
      { inicio: 540, fin: 600 },
      { inicio: 570, fin: 630 },
      { inicio: 585, fin: 615 },
      { inicio: 630, fin: 660 },
    ]);
    expect(resultado.slice(0, 3).every((item) => item.columnas > 1)).toBe(true);
    expect(resultado[3].columnas).toBe(1);
    expect(new Set(resultado.slice(0, 3).map((item) => item.columna)).size).toBeGreaterThan(1);
  });

  it("tolera intervalos contenidos y fallback de 30 minutos", () => {
    const resultado = distribuirSolapamientos([{ inicio: 540, fin: 600 }, { inicio: 550, fin: 580 }, { inicio: 700, fin: 730 }]);
    expect(resultado[0].columnas).toBe(2);
    expect(resultado[1].columnas).toBe(2);
    expect(resultado[2].columnas).toBe(1);
  });
});
