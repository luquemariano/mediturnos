import { beforeEach, describe, expect, it, vi } from "vitest";
import api from "../src/api/api";
import { obtenerMiAgendaProfesional } from "../src/services/turnoService";

vi.mock("../src/api/api", () => ({ default: { get: vi.fn() } }));

describe("contrato de agenda profesional", () => {
  beforeEach(() => vi.clearAllMocks());

  it("omite params sin filtros y conserva la llamada actual", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] });
    await obtenerMiAgendaProfesional();
    expect(api.get).toHaveBeenCalledWith("/profesionales/me/agenda", undefined);
  });

  it("envía rango, estado y encoding mediante params de Axios", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] });
    await obtenerMiAgendaProfesional({ desde: "2026-08-31", hasta: "2026-09-06", estado: "confirmado" });
    expect(api.get).toHaveBeenCalledWith("/profesionales/me/agenda", { params: { desde: "2026-08-31", hasta: "2026-09-06", estado: "confirmado" } });
  });
});
