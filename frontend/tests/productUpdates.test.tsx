import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ACTIVE_PRODUCT_UPDATE, getLatestActiveProductUpdate, PRODUCT_UPDATES } from "../src/productUpdates";
import ProductUpdateCard from "../src/components/ProductUpdateCard";

describe("novedades del producto", () => {
  it("publica WA11B como novedad activa más reciente", () => {
    expect(getLatestActiveProductUpdate()?.id).toBe("wa11b-whatsapp-reminders");
    expect(ACTIVE_PRODUCT_UPDATE).toMatchObject({
      id: "wa11b-whatsapp-reminders",
      title: "Recordatorios automáticos por WhatsApp",
      ctaPath: "/pacientes",
      helpPath: "/ayuda/recordatorios",
      badge: "Nuevo",
      active: true,
    });
  });

  it("muestra la tarjeta WA11B y sus CTAs abren las rutas correspondientes", () => {
    const open = vi.fn();
    render(<ProductUpdateCard onOpen={open} />);
    expect(screen.getByRole("heading", { name: "Recordatorios automáticos por WhatsApp" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Gestionar pacientes" }));
    fireEvent.click(screen.getByRole("button", { name: "Cómo funciona" }));
    expect(open).toHaveBeenNthCalledWith(1, "/pacientes");
    expect(open).toHaveBeenNthCalledWith(2, "/ayuda/recordatorios");
    expect(screen.getByText(/puede recordar los turnos a tus pacientes/)).toBeInTheDocument();
    expect(screen.queryByText(/a todos los pacientes|todos tus pacientes/)).not.toBeInTheDocument();
  });

  it("conserva F12.8 en PRODUCT_UPDATES, pero WA11B permanece activa", () => {
    expect(PRODUCT_UPDATES.find((update) => update.id === "f12-8-public-booking-share")).toMatchObject({
      active: true,
      ctaPath: "/reserva-online",
    });
    expect(getLatestActiveProductUpdate()?.id).toBe("wa11b-whatsapp-reminders");
  });

  it("elige la actualización activa de fecha más reciente y excluye las inactivas", () => {
    const updates = [
      { ...ACTIVE_PRODUCT_UPDATE!, id: "antigua", publishedAt: "2026-01-01", active: true },
      { ...ACTIVE_PRODUCT_UPDATE!, id: "inactiva-reciente", publishedAt: "2027-01-01", active: false },
      { ...ACTIVE_PRODUCT_UPDATE!, id: "activa-reciente", publishedAt: "2026-10-01", active: true },
    ];
    expect(getLatestActiveProductUpdate(updates)?.id).toBe("activa-reciente");
  });
});
