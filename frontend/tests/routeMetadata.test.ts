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
        "Gestioná turnos, pacientes, agenda y recordatorios automáticos por email y WhatsApp desde una sola plataforma. Software para profesionales y consultorios.",
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

  it("indexa la landing de software para consultorios con metadata propia", () => {
    expect(obtenerMetadatosRuta("/software-para-consultorios")).toMatchObject({
      title: "Software para consultorios | Turnelia",
      description: "Gestioná turnos, pacientes, historia clínica, horarios y prestaciones desde una sola plataforma. Turnelia simplifica la gestión diaria de tu consultorio.",
      robots: "index, follow",
      canonical: "https://turnelia.com.ar/software-para-consultorios",
      ogTitle: "Software para consultorios | Turnelia",
      ogUrl: "https://turnelia.com.ar/software-para-consultorios",
      twitterTitle: "Software para consultorios | Turnelia",
    });
  });

  it("indexa la landing de sistema de turnos con metadata propia", () => {
    expect(obtenerMetadatosRuta("/sistema-de-turnos")).toMatchObject({
      title: "Sistema de turnos para consultorios | Turnelia",
      description: "Organizá turnos, horarios y disponibilidad desde una agenda simple. Creá, reprogramá y gestioná citas con Turnelia.",
      robots: "index, follow",
      canonical: "https://turnelia.com.ar/sistema-de-turnos",
      ogUrl: "https://turnelia.com.ar/sistema-de-turnos",
    });
  });

  it("indexa la landing para psicopedagogos con metadata exacta", () => {
    expect(obtenerMetadatosRuta("/para-psicopedagogos")).toMatchObject({
      title: "Software para psicopedagogos | Turnelia",
      description: "Organizá turnos, pacientes, horarios e historias clínicas con Turnelia. Un software simple para psicopedagogos que gestionan su práctica profesional.",
      robots: "index, follow",
      canonical: "https://turnelia.com.ar/para-psicopedagogos",
      ogUrl: "https://turnelia.com.ar/para-psicopedagogos",
    });
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

  it("define metadata social completa para todas las rutas indexables", () => {
    for (const path of ["/", "/software-para-consultorios", "/sistema-de-turnos", "/para-psicopedagogos", "/ayuda", "/terminos", "/privacidad", "/ayuda/agenda"]) {
      const meta = obtenerMetadatosRuta(path);
      expect(meta.ogTitle).toBe(meta.title);
      expect(meta.ogDescription).toBe(meta.description);
      expect(meta.ogUrl).toBe(meta.canonical);
      expect(meta.ogImage).toMatch(/^https:\/\//);
      expect(meta.twitterTitle).toBe(meta.title);
      expect(meta.twitterDescription).toBe(meta.description);
      expect(meta.twitterImage).toBe(meta.ogImage);
    }
  });
});
