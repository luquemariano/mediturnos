import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LegalPage from "../src/legal/LegalPage";
import { obtenerMetadatosRuta } from "../src/seo/routeMetadata";
import { esRutaPublica } from "../src/utils/rutasPublicas";

describe("páginas legales", () => {
  it("renderiza Términos con contacto y navegación legal", () => {
    render(<LegalPage kind="terminos" />);

    expect(screen.getByRole("heading", { level: 1, name: /Términos y Condiciones de Uso de Turnelia/i })).toBeInTheDocument();
    expect(screen.getAllByText(/info@turnelia.com.ar/i).length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "Privacidad" })).toHaveAttribute("href", "/privacidad");
  });

  it("renderiza Privacidad y los derechos de los titulares", () => {
    render(<LegalPage kind="privacidad" />);

    expect(screen.getByRole("heading", { level: 1, name: /Política de Privacidad de Turnelia/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Derechos de los titulares/i })).toBeInTheDocument();
    expect(screen.getAllByText(/Ley N.º 25.326/i).length).toBeGreaterThan(0);
  });

  it("expone metadata indexable y canonical para ambas rutas", () => {
    expect(obtenerMetadatosRuta("/terminos")).toMatchObject({
      title: "Términos y Condiciones | Turnelia",
      robots: "index, follow",
      canonical: "https://turnelia.com.ar/terminos",
    });
    expect(obtenerMetadatosRuta("/privacidad")).toMatchObject({
      title: "Política de Privacidad | Turnelia",
      robots: "index, follow",
      canonical: "https://turnelia.com.ar/privacidad",
    });
  });

  it("considera públicas las rutas legales", () => {
    expect(esRutaPublica("/terminos")).toBe(true);
    expect(esRutaPublica("/privacidad")).toBe(true);
  });
});
