import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const indexHtml = readFileSync(resolve(process.cwd(), "index.html"), "utf8");

function metaContent(selector: string): string {
  const match = indexHtml.match(new RegExp(`<meta\\s+[^>]*${selector}[^>]*content="([^"]+)"[^>]*\\/?\\s*>`));
  expect(match, `No se encontró la etiqueta ${selector}`).not.toBeNull();
  return match?.[1] ?? "";
}

describe("metadata social de la portada", () => {
  it("configura la social card Open Graph y Twitter", () => {
    expect(metaContent('property="og:image"')).toBe("https://turnelia.com.ar/brand/turnelia-social-card.png");
    expect(metaContent('property="og:image:width"')).toBe("1200");
    expect(metaContent('property="og:image:height"')).toBe("630");
    expect(metaContent('name="twitter:card"')).toBe("summary_large_image");
    expect(metaContent('name="twitter:image"')).toBe("https://turnelia.com.ar/brand/turnelia-social-card.png");
  });

  it("conserva la metadata SEO existente y el JSON-LD", () => {
    expect(indexHtml).toContain('<title>Turnelia | Sistema de turnos y gestión para consultorios</title>');
    expect(indexHtml).toContain('name="description"');
    expect(indexHtml).toContain('name="robots" content="index, follow"');
    expect(indexHtml).toContain('rel="canonical" href="https://turnelia.com.ar/"');
    expect(indexHtml).toContain('property="og:title"');
    expect(indexHtml).toContain('property="og:description"');
    expect(indexHtml).toContain('property="og:url"');
    expect(indexHtml).toContain('property="og:site_name"');
    expect(indexHtml).toContain('name="twitter:title"');
    expect(indexHtml).toContain('name="twitter:description"');
    expect(indexHtml).toContain('type="application/ld+json"');
  });
});
