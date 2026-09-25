import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { obtenerMetadatosRuta } from "../src/seo/routeMetadata";

const routes = [
  ["/", "La agenda profesional que ordena tu consulta"],
  ["/software-para-consultorios", "Software para consultorios simple y completo"],
  ["/sistema-de-turnos", "Sistema de turnos para organizar tu agenda profesional"],
  ["/para-psicopedagogos", "Software para psicopedagogos que simplifica tu gestión diaria"],
  ["/ayuda", "Centro de Ayuda"],
  ["/terminos", "Términos y Condiciones de Uso de Turnelia"],
  ["/privacidad", "Política de Privacidad de Turnelia"],
  ...["primeros-pasos", "prestaciones", "disponibilidad", "agenda", "turnos", "pacientes", "historia-clinica", "documentos", "estudios", "recordatorios", "suscripcion", "reserva-online", "reserva-online-paciente", "lista-de-espera", "como-compartir-pagina-reservas"].map((slug) => [`/ayuda/${slug}`, "<h1>"]),
] as const;

function fileFor(path: string) { return resolve(process.cwd(), "dist", path === "/" ? "index.html" : `${path.slice(1)}/index.html`); }

describe("salida HTML prerenderizada", () => {
  it.each(routes)("genera HTML completo para %s", (path, h1) => {
    const file = fileFor(path);
    expect(existsSync(file), `No existe ${file}; ejecutar npm run build`).toBe(true);
    const html = readFileSync(file, "utf8");
    const meta = obtenerMetadatosRuta(path);
    expect(html).toContain(`<title>${meta.title}</title>`);
    expect(html).toContain(`rel="canonical" href="${meta.canonical}"`);
    expect(html).toContain(`name="robots" content="${meta.robots}"`);
    expect(html).toContain(`property="og:url" content="${meta.ogUrl}"`);
    expect(html).toContain(h1);
    if (path !== "/") expect(html).not.toContain('rel="canonical" href="https://turnelia.com.ar/"');
    expect(html).toMatch(/<a\s+[^>]*href="\//);
  });

  it("no duplica JSON-LD global ni de página", () => {
    const html = readFileSync(fileFor("/software-para-consultorios"), "utf8");
    expect(html.match(/application\/ld\+json/g)).toHaveLength(1);
    expect(html).toContain('"@type":"Organization"');
    expect(html).toContain('"logo":"https://turnelia.com.ar/brand/mediturnos-symbol.svg"');
  });
});
