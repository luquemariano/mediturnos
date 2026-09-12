import { describe, expect, it } from "vitest";
import { getHelpArticles, parseHelpFrontmatter, validateHelpArticle } from "./helpContent";

describe("contenido del Centro de Ayuda", () => {
  it("carga todos los artículos actuales con categorías válidas", () => {
    const articulos = getHelpArticles();
    expect(articulos.length).toBeGreaterThan(0);
    articulos.forEach((articulo) => expect(() => validateHelpArticle(articulo)).not.toThrow());
  });

  it("rechaza una categoría inválida", () => {
    const { values, body } = parseHelpFrontmatter("---\nslug: prueba\ntitle: Prueba\ndescription: Prueba\ncategory: invalida\norder: 99\n---\nContenido");
    expect(() => validateHelpArticle({ slug: values.slug, title: values.title, description: values.description, body, order: Number(values.order), category: values.category as never })).toThrow("Artículo de ayuda inválido.");
  });
});
