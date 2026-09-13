import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ACTIVE_PRODUCT_UPDATE, getLatestActiveProductUpdate } from "../src/productUpdates";
import ProductUpdateCard from "../src/components/ProductUpdateCard";

describe("F12.8 novedades", () => {
  it("mantiene F12.7 histórica y publica F12.8 como activa más reciente", () => { expect(getLatestActiveProductUpdate()?.id).toBe("f12-8-public-booking-share"); expect(ACTIVE_PRODUCT_UPDATE?.title).toBe("Nuevo: compartí tu página de reservas"); expect(ACTIVE_PRODUCT_UPDATE?.ctaLabel).toBe("Ir a Reserva online"); expect(ACTIVE_PRODUCT_UPDATE?.ctaPath).toBe("/reserva-online"); expect(ACTIVE_PRODUCT_UPDATE?.helpPath).toBe("/ayuda/como-compartir-pagina-reservas"); expect(ACTIVE_PRODUCT_UPDATE?.active).toBe(true); });
  it("permanece visible y sus CTAs navegan", () => { const open = vi.fn(); const { rerender } = render(<ProductUpdateCard onOpen={open} />); expect(screen.getByRole("heading", { name: /compartí tu página/ })).toBeInTheDocument(); fireEvent.click(screen.getByRole("button", { name: "Ir a Reserva online" })); fireEvent.click(screen.getByRole("button", { name: "Cómo funciona" })); expect(open).toHaveBeenNthCalledWith(1, "/reserva-online"); expect(open).toHaveBeenNthCalledWith(2, "/ayuda/como-compartir-pagina-reservas"); rerender(<ProductUpdateCard onOpen={open} />); expect(screen.getByRole("heading", { name: /compartí tu página/ })).toBeInTheDocument(); });
  it("conserva F12.7 en el catálogo", () => { expect(getLatestActiveProductUpdate([{ ...ACTIVE_PRODUCT_UPDATE!, id: "f12-7-waitlist-discovery", publishedAt: "2026-09-13" }, ACTIVE_PRODUCT_UPDATE!])?.id).toBe("f12-8-public-booking-share"); });
  it("elige la actualización activa más reciente", () => { const latest = { ...ACTIVE_PRODUCT_UPDATE!, id: "f13", publishedAt: "2026-10-01" }; expect(getLatestActiveProductUpdate([ACTIVE_PRODUCT_UPDATE!, latest])?.id).toBe("f13"); });
});
