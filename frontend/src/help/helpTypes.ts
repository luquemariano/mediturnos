export const HELP_CATEGORIES = [
  "primeros-pasos",
  "configuracion",
  "agenda",
  "pacientes",
  "clinica",
  "cuenta",
] as const;

export type HelpCategory = (typeof HELP_CATEGORIES)[number];

export interface HelpArticleMeta {
  slug: string;
  title: string;
  description: string;
  category: HelpCategory;
  order: number;
}

export interface HelpArticle extends HelpArticleMeta {
  body: string;
}
