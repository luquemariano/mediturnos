import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ACTIVE_PRODUCT_UPDATE, getLatestActiveProductUpdate } from "../src/productUpdates";
import ProductUpdateCard from "../src/components/ProductUpdateCard";

describe("F12.7 novedades", () => {
  it("publica la novedad estable y activa", () => { expect(ACTIVE_PRODUCT_UPDATE?.id).toBe("f12-7-waitlist-discovery"); expect(ACTIVE_PRODUCT_UPDATE?.ctaPath).toBe("/lista-espera"); expect(ACTIVE_PRODUCT_UPDATE?.helpPath).toBe("/ayuda/lista-de-espera"); expect(ACTIVE_PRODUCT_UPDATE?.active).toBe(true); });
  it("permanece visible y sus CTAs navegan", () => { const open = vi.fn(); const { rerender } = render(<ProductUpdateCard onOpen={open} />); expect(screen.getByRole("heading", { name: /Lista de espera inteligente/ })).toBeInTheDocument(); fireEvent.click(screen.getByRole("button", { name: "Probar lista de espera" })); fireEvent.click(screen.getByRole("button", { name: "Cómo funciona" })); expect(open).toHaveBeenNthCalledWith(1, "/lista-espera"); expect(open).toHaveBeenNthCalledWith(2, "/ayuda/lista-de-espera"); rerender(<ProductUpdateCard onOpen={open} />); expect(screen.getByRole("heading", { name: /Lista de espera inteligente/ })).toBeInTheDocument(); });
  it("elige la actualización activa más reciente", () => { const latest = { ...ACTIVE_PRODUCT_UPDATE!, id: "f13", publishedAt: "2026-10-01" }; expect(getLatestActiveProductUpdate([ACTIVE_PRODUCT_UPDATE!, latest])?.id).toBe("f13"); });
});
