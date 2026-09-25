import { getHelpArticleBySlug } from "../help/helpContent";

const HOME_TITLE =
  "Turnelia | Sistema de turnos y gestión para consultorios";
const HOME_DESCRIPTION =
  "Gestioná turnos, pacientes, agenda y recordatorios automáticos por email y WhatsApp desde una sola plataforma. Software para profesionales y consultorios.";
const HOME_CANONICAL = "https://turnelia.com.ar/";
const HELP_TITLE = "Centro de Ayuda | Turnelia";
const HELP_DESCRIPTION = "Guías y tutoriales para configurar Turnelia, gestionar turnos, pacientes y tu agenda profesional.";
const SOFTWARE_DESCRIPTION = "Gestioná turnos, pacientes, historia clínica, horarios y prestaciones desde una sola plataforma. Turnelia simplifica la gestión diaria de tu consultorio.";
const TURNOS_DESCRIPTION = "Organizá turnos, horarios y disponibilidad desde una agenda simple. Creá, reprogramá y gestioná citas con Turnelia.";
const PSICOPEDAGOGOS_DESCRIPTION = "Organizá turnos, pacientes, horarios e historias clínicas con Turnelia. Un software simple para psicopedagogos que gestionan su práctica profesional.";
const TERMS_DESCRIPTION = "Consultá los Términos y Condiciones de uso de Turnelia, la plataforma de agenda y gestión profesional.";
const PRIVACY_DESCRIPTION = "Conocé cómo Turnelia trata y protege los datos personales, incluidos los datos vinculados con la gestión profesional y de pacientes.";

export interface RouteMetadata {
  title: string;
  description: string;
  robots: "index, follow" | "noindex, follow" | "noindex, nofollow";
  canonical?: string;
  referrer?: "no-referrer";
  ogTitle: string;
  ogDescription: string;
  ogUrl?: string;
  ogImage: string;
  twitterTitle: string;
  twitterDescription: string;
  twitterImage: string;
}

const SOCIAL_IMAGE = "https://turnelia.com.ar/brand/turnelia-social-card.png";

function metadata(title: string, description: string, robots: RouteMetadata["robots"], canonical?: string, extra: Partial<RouteMetadata> = {}): RouteMetadata {
  return { title, description, robots, ...(canonical ? { canonical } : {}), ogTitle: title, ogDescription: description, ...(canonical ? { ogUrl: canonical } : {}), ogImage: SOCIAL_IMAGE, twitterTitle: title, twitterDescription: description, twitterImage: SOCIAL_IMAGE, ...extra };
}

function esRutaODescendiente(pathname: string, base: string): boolean {
  return pathname === base || pathname.startsWith(`${base}/`);
}

export function obtenerMetadatosRuta(pathname: string): RouteMetadata {
  if (pathname === "/") {
    return metadata(HOME_TITLE, HOME_DESCRIPTION, "index, follow", HOME_CANONICAL);
  }

  if (pathname === "/ayuda") return metadata(HELP_TITLE, HELP_DESCRIPTION, "index, follow", "https://turnelia.com.ar/ayuda");

  if (pathname === "/software-para-consultorios") return metadata("Software para consultorios | Turnelia", SOFTWARE_DESCRIPTION, "index, follow", "https://turnelia.com.ar/software-para-consultorios");

  if (pathname === "/sistema-de-turnos") return metadata("Sistema de turnos para consultorios | Turnelia", TURNOS_DESCRIPTION, "index, follow", "https://turnelia.com.ar/sistema-de-turnos");

  if (pathname === "/para-psicopedagogos") return metadata("Software para psicopedagogos | Turnelia", PSICOPEDAGOGOS_DESCRIPTION, "index, follow", "https://turnelia.com.ar/para-psicopedagogos");

  if (pathname === "/terminos") return metadata("Términos y Condiciones | Turnelia", TERMS_DESCRIPTION, "index, follow", "https://turnelia.com.ar/terminos");

  if (pathname === "/privacidad") return metadata("Política de Privacidad | Turnelia", PRIVACY_DESCRIPTION, "index, follow", "https://turnelia.com.ar/privacidad");

  if (pathname.startsWith("/ayuda/")) {
    const slug = pathname.slice("/ayuda/".length);
    const article = getHelpArticleBySlug(slug);
    return article
      ? metadata(`${article.title} | Centro de Ayuda Turnelia`, article.description, "index, follow", `https://turnelia.com.ar/ayuda/${article.slug}`)
      : metadata("Guía no encontrada | Centro de Ayuda Turnelia", "La guía solicitada no está disponible.", "noindex, nofollow");
  }

  if (pathname === "/login") {
    return metadata("Ingresar | Turnelia", "Acceso a Turnelia para usuarios registrados.", "noindex, follow");
  }

  if (pathname === "/registro") {
    return metadata("Crear cuenta | Turnelia", "Creá tu cuenta profesional en Turnelia.", "noindex, follow");
  }

  if (pathname === "/forgot-password") {
    return metadata("Recuperar contraseña | Turnelia", "Solicitá instrucciones para recuperar el acceso a Turnelia.", "noindex, follow");
  }

  if (pathname === "/reset-password") {
    return metadata("Restablecer contraseña | Turnelia", "Restablecé la contraseña de tu cuenta de Turnelia.", "noindex, nofollow", undefined, { referrer: "no-referrer" });
  }

  if (pathname === "/suscripcion/retorno") {
    return metadata("Retorno de suscripción | Turnelia", "Verificá el estado de tu suscripción de Turnelia.", "noindex, nofollow");
  }

  if (pathname === "/estudios/enviar") return metadata("Solicitud de estudio | Turnelia", "Consulta segura de una solicitud de estudio.", "noindex, nofollow", undefined, { referrer: "no-referrer" });

  if (
    esRutaODescendiente(pathname, "/app")
    || esRutaODescendiente(pathname, "/admin")
    || esRutaODescendiente(pathname, "/onboarding")
  ) {
    return metadata("Área privada | Turnelia", "Área privada de Turnelia.", "noindex, nofollow");
  }

  return metadata("Página no disponible | Turnelia", "La página solicitada no está disponible.", "noindex, nofollow");
}

function obtenerOCrearMeta(nombre: string): HTMLMetaElement {
  let elemento = document.head.querySelector<HTMLMetaElement>(
    `meta[name="${nombre}"]`,
  );

  if (!elemento) {
    elemento = document.createElement("meta");
    elemento.name = nombre;
    document.head.append(elemento);
  }

  return elemento;
}

export function aplicarMetadatosSeo(pathname: string): void {
  const metadatos = obtenerMetadatosRuta(pathname);
  document.title = metadatos.title;
  obtenerOCrearMeta("description").content = metadatos.description;
  obtenerOCrearMeta("robots").content = metadatos.robots;

  const meta = (selector: string, attribute: "name" | "property", key: string, content: string | undefined) => {
    let element = document.head.querySelector<HTMLMetaElement>(selector);
    if (!content) { element?.remove(); return; }
    if (!element) { element = document.createElement("meta"); element.setAttribute(attribute, key); document.head.append(element); }
    element.content = content;
  };
  meta('meta[property="og:title"]', "property", "og:title", metadatos.ogTitle);
  meta('meta[property="og:description"]', "property", "og:description", metadatos.ogDescription);
  meta('meta[property="og:url"]', "property", "og:url", metadatos.ogUrl);
  meta('meta[property="og:image"]', "property", "og:image", metadatos.ogImage);
  meta('meta[name="twitter:title"]', "name", "twitter:title", metadatos.twitterTitle);
  meta('meta[name="twitter:description"]', "name", "twitter:description", metadatos.twitterDescription);
  meta('meta[name="twitter:image"]', "name", "twitter:image", metadatos.twitterImage);

  const canonical = document.head.querySelector<HTMLLinkElement>(
    'link[rel="canonical"]',
  );
  if (metadatos.canonical) {
    const elemento = canonical ?? document.createElement("link");
    elemento.rel = "canonical";
    elemento.href = metadatos.canonical;
    if (!canonical) document.head.append(elemento);
  } else {
    canonical?.remove();
  }

  const referrer = document.head.querySelector<HTMLMetaElement>(
    'meta[name="referrer"]',
  );
  if (metadatos.referrer) {
    const elemento = referrer ?? document.createElement("meta");
    elemento.name = "referrer";
    elemento.content = metadatos.referrer;
    if (!referrer) document.head.append(elemento);
  } else {
    referrer?.remove();
  }
}
