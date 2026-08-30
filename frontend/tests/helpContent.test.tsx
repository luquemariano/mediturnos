import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import HelpMarkdown from "../src/help/components/HelpMarkdown";
import { getHelpArticleBySlug, getHelpArticles, getHelpArticlesByCategory, getNextHelpArticle, getPreviousHelpArticle, parseHelpFrontmatter } from "../src/help/helpContent";

describe("catálogo de ayuda", () => {
  it("carga artículos ordenados y sin slugs duplicados", () => { const articles = getHelpArticles(); expect(articles.length).toBeGreaterThanOrEqual(2); expect(articles.map((a) => a.order)).toEqual([10, 20]); expect(new Set(articles.map((a) => a.slug)).size).toBe(articles.length); });
  it("busca, filtra y navega por slug", () => { expect(getHelpArticleBySlug("primeros-pasos")?.title).toBe("Primeros pasos"); expect(getHelpArticleBySlug("no-existe")).toBeUndefined(); expect(getHelpArticlesByCategory("configuracion")).toHaveLength(1); expect(getPreviousHelpArticle("prestaciones")?.slug).toBe("primeros-pasos"); expect(getNextHelpArticle("primeros-pasos")?.slug).toBe("prestaciones"); });
  it("valida metadata y cuerpo al cargar", () => { for (const article of getHelpArticles()) { expect(article.title).not.toBe(""); expect(article.description).not.toBe(""); expect(article.body).not.toBe(""); } });
  it("rechaza frontmatter malformado, incompleto y desconocido", () => {
    expect(() => parseHelpFrontmatter("---\nslug sin separador\n---\nTexto")).toThrow("malformada");
    expect(() => parseHelpFrontmatter("---\nslug:\n---\nTexto")).toThrow("incompleto");
    expect(() => parseHelpFrontmatter("---\nunknown: valor\n---\nTexto")).toThrow("desconocida");
  });
});

describe("renderer Markdown seguro", () => {
  it("renderiza todos los elementos soportados y bloquea HTML/protocolos inseguros", () => { const { container } = render(<HelpMarkdown content={"# Título\n\nPárrafo **fuerte**, *énfasis*, `código` y [interno](/ayuda).\n\n- Uno\n\n```ts\nconst valor = 1;\n```\n\n> Nota\n\n[externo](https://example.com) [malicioso](javascript:alert(1))\n\n![Texto alternativo](/help/test.webp)\n\n<script>alert(1)</script>"} />); expect(container.querySelector("h1")?.textContent).toBe("Título"); expect(container.querySelector("p")?.textContent).toContain("Párrafo"); expect(container.querySelector("ul li")?.textContent).toBe("Uno"); expect(container.querySelector("strong")?.textContent).toBe("fuerte"); expect(container.querySelector("em")?.textContent).toBe("énfasis"); expect(container.querySelector("p code")?.textContent).toBe("código"); expect(container.querySelector("pre code")?.textContent).toContain("const valor = 1;"); expect(container.querySelector("blockquote")?.textContent).toBe("Nota"); expect(container.querySelector('a[href="/ayuda"]')?.textContent).toBe("interno"); const external = container.querySelector('a[href="https://example.com"]'); expect(external?.getAttribute("target")).toBe("_blank"); expect(external?.getAttribute("rel")).toBe("noopener noreferrer"); expect(container.querySelector("img")?.alt).toBe("Texto alternativo"); expect(container.querySelector('a[href^="javascript:"]')).toBeNull(); expect(container.querySelector("script")).toBeNull(); expect(container.textContent).toContain("malicioso"); });
});
