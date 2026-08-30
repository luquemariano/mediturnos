import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import HelpMarkdown from "../src/help/components/HelpMarkdown";
import { getHelpArticleBySlug, getHelpArticles, getHelpArticlesByCategory, getNextHelpArticle, getPreviousHelpArticle } from "../src/help/helpContent";

describe("catálogo de ayuda", () => {
  it("carga artículos ordenados y sin slugs duplicados", () => { const articles = getHelpArticles(); expect(articles.length).toBeGreaterThanOrEqual(2); expect(articles.map((a) => a.order)).toEqual([10, 20]); expect(new Set(articles.map((a) => a.slug)).size).toBe(articles.length); });
  it("busca, filtra y navega por slug", () => { expect(getHelpArticleBySlug("primeros-pasos")?.title).toBe("Primeros pasos"); expect(getHelpArticleBySlug("no-existe")).toBeUndefined(); expect(getHelpArticlesByCategory("configuracion")).toHaveLength(1); expect(getPreviousHelpArticle("prestaciones")?.slug).toBe("primeros-pasos"); expect(getNextHelpArticle("primeros-pasos")?.slug).toBe("prestaciones"); });
  it("valida metadata y cuerpo al cargar", () => { for (const article of getHelpArticles()) { expect(article.title).not.toBe(""); expect(article.description).not.toBe(""); expect(article.body).not.toBe(""); } });
});

describe("renderer Markdown seguro", () => {
  it("renderiza elementos soportados sin HTML crudo", () => { const { container } = render(<HelpMarkdown content={"# Título\n\nPárrafo **fuerte** y [enlace](/ayuda).\n\n- Uno\n\n![Texto alternativo](/help/test.webp)\n\n<script>alert(1)</script>"} />); expect(container.querySelector("h1")?.textContent).toBe("Título"); expect(container.querySelector("strong")?.textContent).toBe("fuerte"); expect(container.querySelector("img")?.alt).toBe("Texto alternativo"); expect(container.querySelector("script")).toBeNull(); expect(container.textContent).toContain("<script>alert(1)</script>"); });
});
