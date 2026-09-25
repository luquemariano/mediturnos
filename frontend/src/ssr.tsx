import { createElement } from "react";
import { renderToString } from "react-dom/server";
import LandingPage from "./landing/LandingPage";
import SoftwareConsultoriosPage from "./landing/SoftwareConsultoriosPage";
import SistemaTurnosPage from "./landing/SistemaTurnosPage";
import ParaPsicopedagogosPage from "./landing/ParaPsicopedagogosPage";
import LegalPage from "./legal/LegalPage";
import { HelpArticlePage, HelpHome, HelpLayout } from "./help";
import { obtenerMetadatosRuta } from "./seo/routeMetadata";
import { getHelpArticleBySlug, getHelpArticles } from "./help/helpContent";

const routes = ["/", "/software-para-consultorios", "/sistema-de-turnos", "/para-psicopedagogos", "/ayuda", "/terminos", "/privacidad"];
const articleSlugs = getHelpArticles().map((article) => article.slug);
routes.push(...articleSlugs.map((slug) => `/ayuda/${slug}`));

const globalGraph = [
  { "@type": "SoftwareApplication", name: "Turnelia", applicationCategory: "BusinessApplication", operatingSystem: "Web", url: "https://turnelia.com.ar/", description: "Software de gestión de turnos, pacientes y consultorios para profesionales de salud." },
  { "@type": "WebSite", name: "Turnelia", url: "https://turnelia.com.ar/" },
  { "@type": "Organization", name: "Turnelia", url: "https://turnelia.com.ar/", logo: "https://turnelia.com.ar/brand/mediturnos-symbol.svg" },
];

function pageFor(path: string) {
  if (path === "/") return createElement(LandingPage);
  if (path === "/software-para-consultorios") return createElement(SoftwareConsultoriosPage);
  if (path === "/sistema-de-turnos") return createElement(SistemaTurnosPage);
  if (path === "/para-psicopedagogos") return createElement(ParaPsicopedagogosPage);
  if (path === "/terminos" || path === "/privacidad") return createElement(LegalPage, { kind: path.slice(1) as "terminos" | "privacidad" });
  const slug = path === "/ayuda" ? "" : path.slice("/ayuda/".length);
  const content = slug ? createElement(HelpArticlePage, { slug, onHome: () => {}, onOpenArticle: () => {} }) : createElement(HelpHome, { onOpenArticle: () => {} });
  return createElement(HelpLayout, { loggedIn: false }, content);
}

function pageGraph(path: string) {
  const meta = obtenerMetadatosRuta(path);
  const graph: Record<string, unknown>[] = [{ "@type": "WebPage", "@id": meta.canonical, url: meta.canonical, name: meta.title, description: meta.description }];
  if (["/software-para-consultorios", "/sistema-de-turnos", "/para-psicopedagogos"].includes(path)) {
    graph.push({ "@type": "BreadcrumbList", itemListElement: [{ "@type": "ListItem", position: 1, name: "Inicio", item: "https://turnelia.com.ar/" }, { "@type": "ListItem", position: 2, name: meta.title.replace(" | Turnelia", ""), item: meta.canonical }] });
  }
  if (path.startsWith("/ayuda/")) {
    const article = getHelpArticleBySlug(path.slice("/ayuda/".length));
    if (article) graph.push({ "@type": "BreadcrumbList", itemListElement: [{ "@type": "ListItem", position: 1, name: "Centro de Ayuda", item: "https://turnelia.com.ar/ayuda" }, { "@type": "ListItem", position: 2, name: article.title, item: meta.canonical }] });
  }
  return graph;
}

export function renderSeoRoute(path: string): { html: string; metadata: ReturnType<typeof obtenerMetadatosRuta>; jsonLd: string } {
  if (!routes.includes(path)) throw new Error(`Ruta SEO no configurada: ${path}`);
  const metadata = obtenerMetadatosRuta(path);
  const html = renderToString(pageFor(path));
  const jsonLd = JSON.stringify({ "@context": "https://schema.org", "@graph": [...globalGraph, ...pageGraph(path)] }).replace(/</g, "\\u003c");
  return { html, metadata, jsonLd };
}

export function getSeoRoutes(): string[] { return [...routes]; }
