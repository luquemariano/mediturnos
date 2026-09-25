import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { getHelpArticles } from "../src/help/helpContent";
import { obtenerMetadatosRuta } from "../src/seo/routeMetadata";
import { preguntasFrecuentes } from "../src/landing/LandingPage";
import { preguntas as softwareFaq } from "../src/landing/SoftwareConsultoriosPage";
import { preguntas as turnosFaq } from "../src/landing/SistemaTurnosPage";
import { preguntas as psicopedagogosFaq } from "../src/landing/ParaPsicopedagogosPage";

const PUBLIC_ROUTES = ["/", "/software-para-consultorios", "/sistema-de-turnos", "/para-psicopedagogos", "/ayuda", "/terminos", "/privacidad", ...getHelpArticles().map((article) => `/ayuda/${article.slug}`)];
const APPLICATION_ROUTES = new Set(["/", "/software-para-consultorios", "/sistema-de-turnos", "/para-psicopedagogos"]);
const FAQ_ROUTES = new Set(["/", "/software-para-consultorios", "/sistema-de-turnos", "/para-psicopedagogos"]);
const FAQ_DATA = new Map([["/", preguntasFrecuentes], ["/software-para-consultorios", softwareFaq], ["/sistema-de-turnos", turnosFaq], ["/para-psicopedagogos", psicopedagogosFaq]]);
const ORGANIZATION_ID = "https://turnelia.com.ar/#organization";
const WEBSITE_ID = "https://turnelia.com.ar/#website";

function prerenderedHtml(path: string): string {
  const file = resolve(process.cwd(), "dist", path === "/" ? "index.html" : `${path.slice(1)}/index.html`);
  return readFileSync(file, "utf8");
}

function graphFor(path: string): Record<string, unknown>[] {
  const html = prerenderedHtml(path);
  const scripts = [...html.matchAll(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/g)];
  expect(scripts, `${path} debe tener un único JSON-LD prerenderizado`).toHaveLength(1);
  const parsed = JSON.parse(scripts[0][1]) as { "@graph": Record<string, unknown>[] };
  expect(parsed["@graph"]).toBeInstanceOf(Array);
  return parsed["@graph"];
}

function typed(graph: Record<string, unknown>[], type: string) {
  return graph.filter((node) => node["@type"] === type);
}

describe("structured data prerenderizado", () => {
  it.each(PUBLIC_ROUTES)("relaciona Organization, WebSite y WebPage sin duplicados en %s", (path) => {
    const graph = graphFor(path);
    const meta = obtenerMetadatosRuta(path);
    const [organization] = typed(graph, "Organization");
    const [website] = typed(graph, "WebSite");
    const [page] = typed(graph, "WebPage");
    expect(typed(graph, "Organization")).toHaveLength(1);
    expect(typed(graph, "WebSite")).toHaveLength(1);
    expect(typed(graph, "WebPage")).toHaveLength(1);
    expect(organization).toMatchObject({ "@id": ORGANIZATION_ID, name: "Turnelia", url: "https://turnelia.com.ar/" });
    expect(organization.logo).toBe("https://turnelia.com.ar/brand/mediturnos-symbol.svg");
    expect(existsSync(resolve(process.cwd(), "public/brand/mediturnos-symbol.svg"))).toBe(true);
    expect(website).toMatchObject({ "@id": WEBSITE_ID, publisher: { "@id": ORGANIZATION_ID } });
    expect(page).toMatchObject({ "@id": `${meta.canonical}#webpage`, url: meta.canonical, isPartOf: { "@id": WEBSITE_ID }, publisher: { "@id": ORGANIZATION_ID } });
    expect(graphFor(path)).toHaveLength(graph.length);
  });

  it.each(PUBLIC_ROUTES)("limita schemas comerciales y FAQ a sus páginas visibles en %s", (path) => {
    const graph = graphFor(path);
    expect(typed(graph, "SoftwareApplication")).toHaveLength(APPLICATION_ROUTES.has(path) ? 1 : 0);
    expect(typed(graph, "FAQPage")).toHaveLength(FAQ_ROUTES.has(path) ? 1 : 0);
    const serialized = JSON.stringify(graph);
    for (const forbidden of ["aggregateRating", "review", "ratingValue", "offers", "price", "priceCurrency", "downloadUrl", "screenshot", "awards", "numberOfUsers"]) {
      expect(serialized).not.toContain(JSON.stringify(forbidden));
    }
    expect(typed(graph, "Product")).toHaveLength(0);
  });

  it.each([...FAQ_DATA.keys()])("FAQPage refleja las preguntas y respuestas visibles en %s", (path) => {
    const graph = graphFor(path);
    const [faqPage] = typed(graph, "FAQPage");
    const sourceQuestions = FAQ_DATA.get(path)!;
    const entities = faqPage.mainEntity as { "@type": string; name: string; acceptedAnswer: { "@type": string; text: string } }[];
    expect(entities).toEqual(sourceQuestions.map(([name, text]) => ({ "@type": "Question", name, acceptedAnswer: { "@type": "Answer", text } })));
  });

  it.each(["/software-para-consultorios", "/sistema-de-turnos", "/para-psicopedagogos", "/ayuda", ...getHelpArticles().map((article) => `/ayuda/${article.slug}`)])("has canonical breadcrumbs without unintended trailing slashes at %s", (path) => {
    const graph = graphFor(path);
    const [breadcrumb] = typed(graph, "BreadcrumbList");
    expect(typed(graph, "BreadcrumbList")).toHaveLength(1);
    const meta = obtenerMetadatosRuta(path);
    expect(breadcrumb["@id"]).toBe(`${meta.canonical}#breadcrumb`);
    const items = (breadcrumb.itemListElement as { item: string }[]).map((item) => item.item);
    expect(items.at(-1)).toBe(meta.canonical);
    expect(items.every((url) => url === "https://turnelia.com.ar/" || !url.endsWith("/"))).toBe(true);
    if (path.startsWith("/ayuda/")) expect((breadcrumb.itemListElement as { name: string }[]).map((item) => item.name)).toHaveLength(3);
  });

  it("home enlaza directamente a las tres landings con anchors descriptivos", () => {
    const html = prerenderedHtml("/");
    expect(html).toContain('<a href="/software-para-consultorios">software para consultorios</a>');
    expect(html).toContain('<a href="/sistema-de-turnos">sistema de turnos</a>');
    expect(html).toContain('<a href="/para-psicopedagogos">Turnelia para psicopedagogos</a>');
  });

  it("mantiene enlaces descriptivos entre landings comerciales y hacia ayuda", () => {
    const software = prerenderedHtml("/software-para-consultorios");
    expect(software).toContain('href="/sistema-de-turnos"');
    expect(software).toContain('href="/para-psicopedagogos"');
    expect(software).toContain('href="/ayuda/primeros-pasos"');
    expect(prerenderedHtml("/sistema-de-turnos")).toContain('href="/ayuda/turnos"');
    expect(prerenderedHtml("/para-psicopedagogos")).toContain('href="/ayuda/primeros-pasos"');
  });

  it.each(getHelpArticles().map((article) => [`/ayuda/${article.slug}`, article.slug]))("keeps article navigation as real links without JavaScript: %s", (path) => {
    const html = prerenderedHtml(path);
    expect(html).toMatch(/<a\s+href="\/ayuda"/);
    expect(html).toMatch(/<a\s+href="\/ayuda\/[^"]+"/);
  });
});
