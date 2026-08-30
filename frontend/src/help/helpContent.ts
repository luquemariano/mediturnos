import primerosPasos from "./content/primeros-pasos.md?raw";
import prestaciones from "./content/prestaciones.md?raw";
import type { HelpArticle, HelpArticleMeta, HelpCategory } from "./helpTypes";
import { HELP_CATEGORIES } from "./helpTypes";

function parseArticle(source: string): HelpArticle {
  const match = source.match(/^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/);
  if (!match) throw new Error("El artículo de ayuda debe tener frontmatter.");
  const values = Object.fromEntries(match[1].split("\n").filter(Boolean).map((line) => {
    const separator = line.indexOf(":");
    return [line.slice(0, separator).trim(), line.slice(separator + 1).trim()];
  }));
  const meta: HelpArticleMeta = { slug: values.slug, title: values.title, description: values.description, category: values.category as HelpCategory, order: Number(values.order) };
  validateHelpArticle({ ...meta, body: match[2].trim() });
  return { ...meta, body: match[2].trim() };
}

export function validateHelpArticle(article: HelpArticle): void {
  if (!article.slug || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(article.slug)) throw new Error("Slug de ayuda inválido.");
  if (!article.title.trim() || !article.description.trim()) throw new Error("Metadata de ayuda incompleta.");
  if (!HELP_CATEGORIES.includes(article.category) || !Number.isInteger(article.order) || article.order < 0 || !article.body.trim()) throw new Error("Artículo de ayuda inválido.");
}

const ARTICLES: HelpArticle[] = [parseArticle(primerosPasos), parseArticle(prestaciones)].sort((a, b) => a.order - b.order);
const slugs = new Set<string>();
ARTICLES.forEach((article) => { if (slugs.has(article.slug)) throw new Error(`Slug duplicado: ${article.slug}`); slugs.add(article.slug); });

export function getHelpArticles(): HelpArticle[] { return [...ARTICLES]; }
export function getHelpArticleBySlug(slug: string): HelpArticle | undefined { return ARTICLES.find((article) => article.slug === slug); }
export function getHelpArticlesByCategory(category: HelpCategory): HelpArticle[] { return ARTICLES.filter((article) => article.category === category); }
export function getPreviousHelpArticle(slug: string): HelpArticle | undefined { const index = ARTICLES.findIndex((article) => article.slug === slug); return index > 0 ? ARTICLES[index - 1] : undefined; }
export function getNextHelpArticle(slug: string): HelpArticle | undefined { const index = ARTICLES.findIndex((article) => article.slug === slug); return index >= 0 ? ARTICLES[index + 1] : undefined; }
