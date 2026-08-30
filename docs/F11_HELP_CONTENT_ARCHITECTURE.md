# F11.1 · Arquitectura de contenido canónico

La fuente única de ayuda es Markdown simple, versionado dentro de `frontend/src/help/content/`. Cada archivo contiene un frontmatter pequeño (`slug`, `title`, `description`, `category`, `order`) y cuerpo Markdown. El parser local es explícito, sin dependencia nueva ni contenido remoto; valida slug, metadata, categoría, orden y cuerpo al cargar el catálogo.

El catálogo `helpContent.ts` importa Markdown con Vite `?raw`, ordena de forma determinística y expone lookup por slug, categoría y navegación anterior/siguiente. Los artículos iniciales (`primeros-pasos.md` y `prestaciones.md`) son contenido preliminar para probar la arquitectura y se ampliarán en F11.3.

`HelpMarkdown` renderiza headings, párrafos, listas, links, strong, emphasis, inline code, bloques de código, blockquotes e imágenes con `alt`. No habilita HTML crudo, `dangerouslySetInnerHTML`, scripts, iframes ni handlers. Los enlaces externos se abren con `rel="noopener noreferrer"`.

La página imprime el H1 desde metadata y el cuerpo Markdown no repite el título; así se evita duplicar H1 y se reutiliza la misma metadata para SEO y PDF.

Las imágenes futuras vivirán en `frontend/public/help/` y se referenciarán como `/help/<área>/<archivo>.webp`. F11.2 consumirá el mismo catálogo desde el routing manual existente, sin React Router; allí se incorporarán rutas y metadata SEO. F11.8 podrá reutilizar el renderer y estilos de impresión para producir PDF reproducible con Playwright/Chromium.
