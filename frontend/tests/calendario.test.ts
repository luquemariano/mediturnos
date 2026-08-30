import { describe, expect, it } from "vitest";
import { claveFechaNegocio } from "../src/utils/fechaTurno";
import { diaAnterior, diaSiguiente, diasGrillaMes, diasSemana, finSemana, inicioSemana, mesAnterior, mesSiguiente, primerDiaMes, ultimoDiaMes } from "../src/utils/calendario";

describe("calendario civil de negocio", () => {
  it("navega días y bordes de año", () => {
    expect(diaAnterior("2026-01-01")).toBe("2025-12-31");
    expect(diaSiguiente("2025-12-31")).toBe("2026-01-01");
  });
  it("calcula semanas lunes-domingo incluso al cruzar año", () => {
    expect(inicioSemana("2025-12-31")).toBe("2025-12-29");
    expect(finSemana("2025-12-31")).toBe("2026-01-04");
    expect(diasSemana("2025-12-31")).toEqual(["2025-12-29", "2025-12-30", "2025-12-31", "2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]);
  });
  it("calcula meses de 28, 29, 30 y 31 días y sus grillas", () => {
    expect(ultimoDiaMes("2026-02-01")).toBe("2026-02-28");
    expect(ultimoDiaMes("2024-02-01")).toBe("2024-02-29");
    expect(ultimoDiaMes("2026-04-01")).toBe("2026-04-30");
    expect(ultimoDiaMes("2026-01-01")).toBe("2026-01-31");
    expect(diasGrillaMes("2026-01-01").length).toBe(35);
    expect(diasGrillaMes("2026-08-01").length).toBe(42);
  });
  it("navega meses y respeta Buenos Aires cerca de medianoche UTC", () => {
    expect(primerDiaMes("2026-01-15")).toBe("2026-01-01");
    expect(mesAnterior("2026-01-15")).toBe("2025-12-01");
    expect(mesSiguiente("2025-12-15")).toBe("2026-01-01");
    expect(claveFechaNegocio("2026-08-16T02:30:00Z")).toBe("2026-08-15");
  });
});
