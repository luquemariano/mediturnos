import { afterEach, describe, expect, it } from "vitest";

import {
  aplicarMetadatosSeo,
  obtenerMetadatosRuta,
} from "../src/seo/routeMetadata";

afterEach(() => {
  document.head.querySelector('link[rel="canonical"]')?.remove();
  document.head.querySelector('meta[name="referrer"]')?.remove();
});

describe("metadatos SEO por ruta", () => {
  it("indexa la portada con canonical propio", () => {
    expect(obtenerMetadatosRuta("/")).toMatchObject({
      title: "Turnelia | Sistema de turnos y gestión para consultorios",
      description:
        "Gestioná turnos, pacientes, historias clínicas, horarios y prestaciones desde una sola plataforma. Software de gestión para profesionales y consultorios.",
      robots: "index, follow",
      canonical: "https://turnelia.com.ar/",
    });
  });

  it.each([
    ["/login", "noindex, follow"],
    ["/registro", "noindex, follow"],
    ["/forgot-password", "noindex, follow"],
    ["/reset-password", "noindex, nofollow"],
    ["/app", "noindex, nofollow"],
    ["/app/agenda", "noindex, nofollow"],
    ["/admin/cuentas", "noindex, nofollow"],
    ["/onboarding/perfil", "noindex, nofollow"],
  ])("aplica la política de %s", (ruta, robots) => {
    expect(obtenerMetadatosRuta(ruta).robots).toBe(robots);
  });

  it("actualiza y limpia los elementos del head al navegar", () => {
    aplicarMetadatosSeo("/reset-password");
    expect(document.title).toBe("Restablecer contraseña | Turnelia");
    expect(document.querySelector('meta[name="robots"]')).toHaveAttribute(
      "content",
      "noindex, nofollow",
    );
    expect(document.querySelector('meta[name="referrer"]')).toHaveAttribute(
      "content",
      "no-referrer",
    );
    expect(document.querySelector('link[rel="canonical"]')).toBeNull();

    aplicarMetadatosSeo("/");
    expect(document.querySelector('meta[name="robots"]')).toHaveAttribute(
      "content",
      "index, follow",
    );
    expect(document.querySelector('link[rel="canonical"]')).toHaveAttribute(
      "href",
      "https://turnelia.com.ar/",
    );
    expect(document.querySelector('meta[name="referrer"]')).toBeNull();
  });
});
