const HOME_TITLE =
  "Software de turnos para profesionales de salud | Turnelia";
const HOME_DESCRIPTION =
  "Gestioná turnos, pacientes, horarios y prestaciones desde una sola plataforma. Turnelia simplifica la organización diaria de profesionales y consultorios.";
const HOME_CANONICAL = "https://turnelia.com.ar/";

export interface RouteMetadata {
  title: string;
  description: string;
  robots: "index, follow" | "noindex, follow" | "noindex, nofollow";
  canonical?: string;
  referrer?: "no-referrer";
}

function esRutaODescendiente(pathname: string, base: string): boolean {
  return pathname === base || pathname.startsWith(`${base}/`);
}

export function obtenerMetadatosRuta(pathname: string): RouteMetadata {
  if (pathname === "/") {
    return {
      title: HOME_TITLE,
      description: HOME_DESCRIPTION,
      robots: "index, follow",
      canonical: HOME_CANONICAL,
    };
  }

  if (pathname === "/login") {
    return {
      title: "Ingresar | Turnelia",
      description: "Acceso a Turnelia para usuarios registrados.",
      robots: "noindex, follow",
    };
  }

  if (pathname === "/registro") {
    return {
      title: "Crear cuenta | Turnelia",
      description: "Creá tu cuenta profesional en Turnelia.",
      robots: "noindex, follow",
    };
  }

  if (pathname === "/forgot-password") {
    return {
      title: "Recuperar contraseña | Turnelia",
      description: "Solicitá instrucciones para recuperar el acceso a Turnelia.",
      robots: "noindex, follow",
    };
  }

  if (pathname === "/reset-password") {
    return {
      title: "Restablecer contraseña | Turnelia",
      description: "Restablecé la contraseña de tu cuenta de Turnelia.",
      robots: "noindex, nofollow",
      referrer: "no-referrer",
    };
  }

  if (
    esRutaODescendiente(pathname, "/app")
    || esRutaODescendiente(pathname, "/admin")
    || esRutaODescendiente(pathname, "/onboarding")
  ) {
    return {
      title: "Área privada | Turnelia",
      description: "Área privada de Turnelia.",
      robots: "noindex, nofollow",
    };
  }

  return {
    title: "Página no disponible | Turnelia",
    description: "La página solicitada no está disponible.",
    robots: "noindex, nofollow",
  };
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
