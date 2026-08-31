import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import HelpMarkdown from "../src/help/components/HelpMarkdown";
import HelpHome from "../src/help/components/HelpHome";
import HelpArticlePage from "../src/help/components/HelpArticlePage";
import { getHelpArticleBySlug, getHelpArticles, getHelpArticlesByCategory, getNextHelpArticle, getPreviousHelpArticle, parseHelpFrontmatter } from "../src/help/helpContent";
import { debeForzarOnboarding, esRutaPublica } from "../src/utils/rutasPublicas";

describe("catálogo de ayuda", () => {
  it("carga los once artículos ordenados y sin slugs duplicados", () => { const articles = getHelpArticles(); expect(articles.map((a) => a.order)).toEqual([10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]); expect(articles.map((a) => a.slug)).toEqual(["primeros-pasos", "prestaciones", "disponibilidad", "agenda", "turnos", "pacientes", "historia-clinica", "documentos", "estudios", "recordatorios", "suscripcion"]); expect(new Set(articles.map((a) => a.slug)).size).toBe(articles.length); });
  it("busca, filtra y navega por slug", () => { expect(getHelpArticleBySlug("primeros-pasos")?.title).toBe("Primeros pasos"); expect(getHelpArticleBySlug("no-existe")).toBeUndefined(); expect(getHelpArticlesByCategory("configuracion")).toHaveLength(2); expect(getHelpArticlesByCategory("pacientes")).toHaveLength(1); expect(getHelpArticlesByCategory("clinica")).toHaveLength(3); expect(getHelpArticlesByCategory("agenda")).toHaveLength(3); expect(getHelpArticlesByCategory("cuenta")).toHaveLength(1); expect(getPreviousHelpArticle("prestaciones")?.slug).toBe("primeros-pasos"); expect(getNextHelpArticle("turnos")?.slug).toBe("pacientes"); expect(getNextHelpArticle("pacientes")?.slug).toBe("historia-clinica"); expect(getNextHelpArticle("historia-clinica")?.slug).toBe("documentos"); expect(getNextHelpArticle("documentos")?.slug).toBe("estudios"); expect(getNextHelpArticle("estudios")?.slug).toBe("recordatorios"); expect(getNextHelpArticle("recordatorios")?.slug).toBe("suscripcion"); });
  it("valida metadata y cuerpo al cargar", () => { for (const article of getHelpArticles()) { expect(article.title).not.toBe(""); expect(article.description).not.toBe(""); expect(article.body).not.toBe(""); } });
  it("contiene guías funcionales sin el placeholder inicial", () => { const primeros = getHelpArticleBySlug("primeros-pasos")?.body ?? ""; const prestaciones = getHelpArticleBySlug("prestaciones")?.body ?? ""; const disponibilidad = getHelpArticleBySlug("disponibilidad")?.body ?? ""; const agenda = getHelpArticleBySlug("agenda")?.body ?? ""; const turnos = getHelpArticleBySlug("turnos")?.body ?? ""; const pacientes = getHelpArticleBySlug("pacientes")?.body ?? ""; const clinica = getHelpArticleBySlug("historia-clinica")?.body ?? ""; const documentos = getHelpArticleBySlug("documentos")?.body ?? ""; const estudios = getHelpArticleBySlug("estudios")?.body ?? ""; const recordatorios = getHelpArticleBySlug("recordatorios")?.body ?? ""; const suscripcion = getHelpArticleBySlug("suscripcion")?.body ?? ""; expect(primeros).toContain("## 1. Crear la cuenta"); expect(primeros).toContain("/ayuda/prestaciones"); expect(primeros).not.toContain("primera versión"); expect(prestaciones).toContain("## Crear una prestación"); expect(prestaciones).toContain("## Desactivar una prestación"); expect(prestaciones).toContain("turnos ya creados"); expect(disponibilidad).toContain("## Varias franjas en un mismo día"); expect(disponibilidad).toContain("no cancela automáticamente"); expect(agenda).toContain("## Vista Día"); expect(agenda).toContain("## Vista Semana"); expect(agenda).toContain("## Vista Mes"); expect(turnos).toContain("## Crear un turno"); expect(pacientes).toContain("## Crear un paciente"); expect(pacientes).toContain("## Desactivar un paciente"); expect(pacientes).toContain("Historial de turnos"); expect(clinica).toContain("## Resumen clínico"); expect(clinica).toContain("## Agregar una evolución"); expect(clinica).toContain("no se edita ni se reemplaza"); expect(documentos).toContain("PDF, JPG, JPEG, PNG y WebP"); expect(documentos).toContain("10 MB"); expect(documentos).toContain("## Privacidad"); expect(estudios).toContain("## Crear una solicitud"); expect(estudios).toContain("## Qué puede hacer el paciente"); expect(estudios).toContain("hasta 5 archivos"); expect(estudios).toContain("Resultados enviados"); expect(estudios).toContain("Requiere consulta presencial"); expect(recordatorios).toContain("24 horas previas"); expect(recordatorios).toContain("Pendiente"); expect(recordatorios).toContain("no garantiza"); expect(suscripcion).toContain("independiente del precio"); expect(suscripcion).toContain("Mercado Pago"); expect(suscripcion).toContain("14 días"); });
  it("rechaza frontmatter malformado, incompleto y desconocido", () => {
    expect(() => parseHelpFrontmatter("---\nslug sin separador\n---\nTexto")).toThrow("malformada");
    expect(() => parseHelpFrontmatter("---\nslug:\n---\nTexto")).toThrow("incompleto");
    expect(() => parseHelpFrontmatter("---\nunknown: valor\n---\nTexto")).toThrow("desconocida");
  });
});

describe("renderer Markdown seguro", () => {
  it("renderiza todos los elementos soportados y bloquea HTML/protocolos inseguros", () => { const { container } = render(<HelpMarkdown content={"# Título\n\nPárrafo **fuerte**, *énfasis*, `código` y [interno](/ayuda).\n\n- Uno\n\n1. Paso uno\n2. Paso dos\n\n```ts\nconst valor = 1;\n```\n\n> Nota\n\n[externo](https://example.com) [malicioso](javascript:alert(1))\n\n![Texto alternativo](/help/test.webp)\n\n<script>alert(1)</script>"} />); expect(container.querySelector("h1")?.textContent).toBe("Título"); expect(container.querySelector("p")?.textContent).toContain("Párrafo"); expect(container.querySelector("ul li")?.textContent).toBe("Uno"); expect(container.querySelector("ol li")?.textContent).toBe("Paso uno"); expect(container.querySelector("strong")?.textContent).toBe("fuerte"); expect(container.querySelector("em")?.textContent).toBe("énfasis"); expect(container.querySelector("p code")?.textContent).toBe("código"); expect(container.querySelector("pre code")?.textContent).toContain("const valor = 1;"); expect(container.querySelector("blockquote")?.textContent).toBe("Nota"); expect(container.querySelector('a[href="/ayuda"]')?.textContent).toBe("interno"); const external = container.querySelector('a[href="https://example.com"]'); expect(external?.getAttribute("target")).toBe("_blank"); expect(external?.getAttribute("rel")).toBe("noopener noreferrer"); expect(container.querySelector("img")?.alt).toBe("Texto alternativo"); expect(container.querySelector('a[href^="javascript:"]')).toBeNull(); expect(container.querySelector("script")).toBeNull(); expect(container.textContent).toContain("malicioso"); });
});

describe("páginas públicas de ayuda", () => {
  it("muestra portada, artículo y 404 sin autenticación", () => {
    const home = render(<HelpHome onOpenArticle={() => undefined} />);
    expect(home.getByRole("heading", { name: "Centro de Ayuda" })).toBeTruthy();
    expect(home.getByText("Primeros pasos")).toBeTruthy();
    home.unmount();
    const article = render(<HelpArticlePage slug="primeros-pasos" onHome={() => undefined} onOpenArticle={() => undefined} />);
    expect(article.getByRole("heading", { name: "Primeros pasos" })).toBeTruthy();
    expect(article.getByRole("navigation", { name: "Migas de pan" })).toBeTruthy();
    article.unmount();
    const missing = render(<HelpArticlePage slug="no-existe" onHome={() => undefined} onOpenArticle={() => undefined} />);
    expect(missing.getByRole("heading", { name: "No encontramos esta guía" })).toBeTruthy();
    expect(missing.getByRole("button", { name: "Volver al Centro de Ayuda" })).toBeTruthy();
  });
});

describe("política de rutas durante restauración", () => {
  it("preserva la ayuda y demás rutas públicas", () => {
    for (const path of ["/", "/ayuda", "/ayuda/primeros-pasos", "/ayuda/no-existe", "/estudios/enviar", "/suscripcion/retorno", "/login", "/registro", "/forgot-password", "/reset-password"]) {
      expect(esRutaPublica(path)).toBe(true);
      expect(debeForzarOnboarding(path)).toBe(false);
    }
  });
  it("sólo fuerza onboarding en rutas no públicas fuera del onboarding", () => {
    expect(debeForzarOnboarding("/app")).toBe(true);
    expect(debeForzarOnboarding("/app/pacientes")).toBe(true);
    expect(debeForzarOnboarding("/onboarding/perfil")).toBe(false);
  });
});
