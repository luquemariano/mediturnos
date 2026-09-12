import { describe, expect, it, vi } from "vitest";
import api from "../src/api/api";
import { obtenerAdopcionAdmin } from "../src/services/adminAdoptionService";

vi.mock("../src/api/api", () => ({ default: { get: vi.fn() } }));

describe("servicio de adopción administrativa", () => {
  it("consulta el endpoint con filtros", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] });
    await obtenerAdopcionAdmin({ status: "activo", q: "ana" });
    expect(api.get).toHaveBeenCalledWith("/admin/adoption", { params: { status: "activo", q: "ana" }, signal: undefined });
  });
});
