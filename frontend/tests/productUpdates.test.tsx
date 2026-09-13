import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ACTIVE_PRODUCT_UPDATE, productUpdateStorageKey } from "../src/productUpdates";
import ProductUpdateCard from "../src/components/ProductUpdateCard";

describe("F12.7 novedades", () => {
  beforeEach(() => localStorage.clear());
  it("publica la novedad estable y activa", () => { expect(ACTIVE_PRODUCT_UPDATE?.id).toBe("f12-7-waitlist-discovery"); expect(ACTIVE_PRODUCT_UPDATE?.ctaPath).toBe("/lista-espera"); expect(ACTIVE_PRODUCT_UPDATE?.helpPath).toBe("/ayuda/lista-de-espera"); expect(ACTIVE_PRODUCT_UPDATE?.active).toBe(true); });
  it("navega y persiste cierre por profesional", () => { const open = vi.fn(); const { rerender } = render(<ProductUpdateCard userKey="42" onOpen={open} />); expect(screen.getByRole("heading", { name: /Lista de espera inteligente/ })).toBeInTheDocument(); fireEvent.click(screen.getByRole("button", { name: "Probar lista de espera" })); expect(open).toHaveBeenCalledWith("/lista-espera"); expect(localStorage.getItem(productUpdateStorageKey("f12-7-waitlist-discovery", "42"))).toBe("dismissed"); rerender(<ProductUpdateCard userKey="42" onOpen={open} />); expect(screen.queryByRole("heading", { name: /Lista de espera inteligente/ })).toBeNull(); });
  it("abre la ayuda desde el CTA secundario", () => { const open = vi.fn(); render(<ProductUpdateCard userKey="43" onOpen={open} />); fireEvent.click(screen.getByRole("button", { name: "Cómo funciona" })); expect(open).toHaveBeenCalledWith("/ayuda/lista-de-espera"); });
});
