import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import BajaNovedades from "../src/pages/BajaNovedades";
import { extraerYLimpiarTokenBaja } from "../src/utils/tokenBajaNovedades";

const { post } = vi.hoisted(() => ({ post: vi.fn() }));
vi.mock("axios", () => ({ default: { post } }));

describe("BajaNovedades", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.history.replaceState({}, "", "/baja-novedades#signed-token");
    post.mockResolvedValue({ data: { baja_realizada: true } });
  });

  it("lee el token del fragmento y lo limpia de la URL inmediatamente", () => {
    window.history.replaceState({}, "", "/baja-novedades?origen=email#signed-token");
    expect(extraerYLimpiarTokenBaja()).toBe("signed-token");
    expect(window.location.href).not.toContain("signed-token");
    expect(window.location.search).toBe("?origen=email");
  });

  it("confirma la baja con un POST del token en el cuerpo y sin petición previa", async () => {
    const token = extraerYLimpiarTokenBaja();
    render(<BajaNovedades token={token} />);
    expect(await screen.findByRole("heading", { name: "Darse de baja" })).toBeInTheDocument();
    expect(window.location.href).not.toContain("signed-token");
    expect(post).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Confirmar baja" }));
    expect(await screen.findByRole("heading", { name: "Baja confirmada" })).toBeInTheDocument();
    expect(post).toHaveBeenCalledWith(expect.stringContaining("/public/baja-novedades"), { token: "signed-token" });
  });

  it("no interpreta un token en query string", () => {
    window.history.replaceState({}, "", "/baja-novedades?token=query-token");
    expect(extraerYLimpiarTokenBaja()).toBeNull();
    expect(window.location.href).not.toContain("query-token");
  });
});
