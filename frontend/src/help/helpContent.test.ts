import { describe, expect, it } from "vitest";
import { getHelpArticleBySlug, getHelpArticles, parseHelpFrontmatter, validateHelpArticle } from "./helpContent";

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

  it("publica el artículo operativo de recordatorios por WhatsApp", () => {
    const articulo = getHelpArticleBySlug("recordatorios");
    expect(articulo).toBeDefined();
    expect(articulo?.title).toBe("Recordatorios automáticos por email y WhatsApp");
    expect(articulo?.description).toMatch(/WhatsApp/);
    expect(articulo?.body).toMatch(/confirm/i);
    expect(articulo?.body).toMatch(/cancel/i);
    expect(articulo?.body).toMatch(/email y WhatsApp son canales independientes|ambos pueden coexistir/i);
    expect(articulo?.body).toMatch(/reprogramación desde WhatsApp no está disponible/i);
    expect(articulo?.body).toContain("/ayuda/lista-de-espera");
    expect(articulo?.body).not.toMatch(/reprogramación desde WhatsApp (está disponible|ya está disponible)/i);
  });
});
