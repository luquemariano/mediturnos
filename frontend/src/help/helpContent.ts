import primerosPasos from "./content/primeros-pasos.md?raw";
import prestaciones from "./content/prestaciones.md?raw";
import disponibilidad from "./content/disponibilidad.md?raw";
import agenda from "./content/agenda.md?raw";
import turnos from "./content/turnos.md?raw";
import pacientes from "./content/pacientes.md?raw";
import historiaClinica from "./content/historia-clinica.md?raw";
import documentos from "./content/documentos.md?raw";
import estudios from "./content/estudios.md?raw";
import recordatorios from "./content/recordatorios.md?raw";
import suscripcion from "./content/suscripcion.md?raw";
import type { HelpArticle, HelpArticleMeta, HelpCategory } from "./helpTypes";
import { HELP_CATEGORIES } from "./helpTypes";

const FRONTMATTER_KEYS = new Set(["slug", "title", "description", "category", "order"]);

export function parseHelpFrontmatter(source: string): { values: Record<string, string>; body: string } {
  const match = source.match(/^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/);
  if (!match) throw new Error("El artículo de ayuda debe tener frontmatter.");
  const values: Record<string, string> = {};
  match[1].split("\n").forEach((line) => {
    if (!line.trim()) return;
    const separator = line.indexOf(":");
    if (separator < 0) throw new Error("Línea de frontmatter malformada.");
    const key = line.slice(0, separator).trim();
    const value = line.slice(separator + 1).trim();
    if (!key || !value) throw new Error("Frontmatter incompleto.");
    if (!FRONTMATTER_KEYS.has(key)) throw new Error(`Clave de frontmatter desconocida: ${key}`);
    if (key in values) throw new Error(`Clave de frontmatter duplicada: ${key}`);
    values[key] = value;
  });
  return { values, body: match[2].trim() };
}

function parseArticle(source: string): HelpArticle {
  const { values, body } = parseHelpFrontmatter(source);
  const meta: HelpArticleMeta = { slug: values.slug, title: values.title, description: values.description, category: values.category as HelpCategory, order: Number(values.order) };
  validateHelpArticle({ ...meta, body });
  return { ...meta, body };
}

export function validateHelpArticle(article: HelpArticle): void {
  if (!article.slug || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(article.slug)) throw new Error("Slug de ayuda inválido.");
  if (typeof article.title !== "string" || typeof article.description !== "string" || !article.title.trim() || !article.description.trim()) throw new Error("Metadata de ayuda incompleta.");
  if (!HELP_CATEGORIES.includes(article.category) || !Number.isInteger(article.order) || article.order < 0 || !article.body.trim()) throw new Error("Artículo de ayuda inválido.");
}

const ARTICLES: HelpArticle[] = [parseArticle(primerosPasos), parseArticle(prestaciones), parseArticle(disponibilidad), parseArticle(agenda), parseArticle(turnos), parseArticle(pacientes), parseArticle(historiaClinica), parseArticle(documentos), parseArticle(estudios), parseArticle(recordatorios), parseArticle(suscripcion)].sort((a, b) => a.order - b.order);
const slugs = new Set<string>();
ARTICLES.forEach((article) => { if (slugs.has(article.slug)) throw new Error(`Slug duplicado: ${article.slug}`); slugs.add(article.slug); });

export function getHelpArticles(): HelpArticle[] { return [...ARTICLES]; }
export function getHelpArticleBySlug(slug: string): HelpArticle | undefined { return ARTICLES.find((article) => article.slug === slug); }
export function getHelpArticlesByCategory(category: HelpCategory): HelpArticle[] { return ARTICLES.filter((article) => article.category === category); }
export function getPreviousHelpArticle(slug: string): HelpArticle | undefined { const index = ARTICLES.findIndex((article) => article.slug === slug); return index > 0 ? ARTICLES[index - 1] : undefined; }
export function getNextHelpArticle(slug: string): HelpArticle | undefined { const index = ARTICLES.findIndex((article) => article.slug === slug); return index >= 0 ? ARTICLES[index + 1] : undefined; }
