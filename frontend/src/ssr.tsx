import { createElement } from "react";
import { renderToString } from "react-dom/server";
import LandingPage, { preguntasFrecuentes } from "./landing/LandingPage";
import SoftwareConsultoriosPage, { preguntas as softwareFaq } from "./landing/SoftwareConsultoriosPage";
import SistemaTurnosPage, { preguntas as turnosFaq } from "./landing/SistemaTurnosPage";
import ParaPsicopedagogosPage, { preguntas as psicopedagogosFaq } from "./landing/ParaPsicopedagogosPage";
import LegalPage from "./legal/LegalPage";
import { HelpArticlePage, HelpHome, HelpLayout } from "./help";
import { obtenerMetadatosRuta } from "./seo/routeMetadata";
import { getHelpArticleBySlug, getHelpArticles } from "./help/helpContent";

const routes = ["/", "/software-para-consultorios", "/sistema-de-turnos", "/para-psicopedagogos", "/ayuda", "/terminos", "/privacidad"];
const articleSlugs = getHelpArticles().map((article) => article.slug);
routes.push(...articleSlugs.map((slug) => `/ayuda/${slug}`));

const ORGANIZATION_ID = "https://turnelia.com.ar/#organization";
const WEBSITE_ID = "https://turnelia.com.ar/#website";
const SOFTWARE_APPLICATION_ID = "https://turnelia.com.ar/#software-application";
const organization = { "@type": "Organization", "@id": ORGANIZATION_ID, name: "Turnelia", url: "https://turnelia.com.ar/", logo: "https://turnelia.com.ar/brand/mediturnos-symbol.svg" };
const website = { "@type": "WebSite", "@id": WEBSITE_ID, url: "https://turnelia.com.ar/", name: "Turnelia", publisher: { "@id": ORGANIZATION_ID } };
const softwareApplication = { "@type": "SoftwareApplication", "@id": SOFTWARE_APPLICATION_ID, name: "Turnelia", applicationCategory: "BusinessApplication", operatingSystem: "Web", url: "https://turnelia.com.ar/", provider: { "@id": ORGANIZATION_ID } };
const applicationRoutes = new Set(["/", "/software-para-consultorios", "/sistema-de-turnos", "/para-psicopedagogos"]);
const faqByRoute = new Map<string, readonly (readonly [string, string])[]>([
  ["/", preguntasFrecuentes],
  ["/software-para-consultorios", softwareFaq],
  ["/sistema-de-turnos", turnosFaq],
  ["/para-psicopedagogos", psicopedagogosFaq],
]);

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
  const canonical = meta.canonical!;
  const graph: Record<string, unknown>[] = [
    organization,
    website,
    { "@type": "WebPage", "@id": `${canonical}#webpage`, url: canonical, name: meta.title, description: meta.description, isPartOf: { "@id": WEBSITE_ID }, publisher: { "@id": ORGANIZATION_ID }, ...(applicationRoutes.has(path) ? { about: { "@id": SOFTWARE_APPLICATION_ID } } : {}) },
  ];
  if (applicationRoutes.has(path)) graph.push(softwareApplication);

  let breadcrumbItems: { name: string; item: string }[] | undefined;
  if (path === "/ayuda") {
    breadcrumbItems = [{ name: "Inicio", item: "https://turnelia.com.ar/" }, { name: "Centro de Ayuda", item: canonical }];
  } else if (["/software-para-consultorios", "/sistema-de-turnos", "/para-psicopedagogos"].includes(path)) {
    breadcrumbItems = [{ name: "Inicio", item: "https://turnelia.com.ar/" }, { name: meta.title.replace(" | Turnelia", ""), item: canonical }];
  } else if (path.startsWith("/ayuda/")) {
    const article = getHelpArticleBySlug(path.slice("/ayuda/".length));
    if (article) breadcrumbItems = [{ name: "Inicio", item: "https://turnelia.com.ar/" }, { name: "Centro de Ayuda", item: "https://turnelia.com.ar/ayuda" }, { name: article.title, item: canonical }];
  }
  if (breadcrumbItems) graph.push({ "@type": "BreadcrumbList", "@id": `${canonical}#breadcrumb`, itemListElement: breadcrumbItems.map(({ name, item }, index) => ({ "@type": "ListItem", position: index + 1, name, item })) });

  const faq = faqByRoute.get(path);
  if (faq) graph.push({ "@type": "FAQPage", "@id": `${canonical}#faq`, mainEntity: faq.map(([name, text]) => ({ "@type": "Question", name, acceptedAnswer: { "@type": "Answer", text } })) });
  return graph;
}

export function renderSeoRoute(path: string): { html: string; metadata: ReturnType<typeof obtenerMetadatosRuta>; jsonLd: string } {
  if (!routes.includes(path)) throw new Error(`Ruta SEO no configurada: ${path}`);
  const metadata = obtenerMetadatosRuta(path);
  const html = renderToString(pageFor(path));
  const jsonLd = JSON.stringify({ "@context": "https://schema.org", "@graph": pageGraph(path) }).replace(/</g, "\\u003c");
  return { html, metadata, jsonLd };
}

export function getSeoRoutes(): string[] { return [...routes]; }
