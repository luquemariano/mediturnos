import { readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const dist = resolve("dist");
const template = await readFile(resolve(dist, "index.html"), "utf8");
const ssrOutput = resolve(dist, "ssr-build", "ssr.js");
const { getSeoRoutes, renderSeoRoute } = await import(pathToFileURL(ssrOutput).href);

function escapeHtml(value) {
  return value.replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function updateMeta(html, selector, tag) {
  const pattern = new RegExp(`<meta\\s+[^>]*${selector}[^>]*>`, "i");
  return pattern.test(html) ? html.replace(pattern, tag) : html.replace("</head>", `    ${tag}\n  </head>`);
}

for (const route of getSeoRoutes()) {
  const { html: appHtml, metadata, jsonLd } = renderSeoRoute(route);
  let html = template.replace("<!--app-html-->", appHtml);
  html = html.replace(/<title>[\s\S]*?<\/title>/i, `<title>${escapeHtml(metadata.title)}</title>`);
  html = updateMeta(html, 'name="description"', `<meta name="description" content="${escapeHtml(metadata.description)}" />`);
  html = updateMeta(html, 'name="robots"', `<meta name="robots" content="${metadata.robots}" />`);
  html = updateMeta(html, 'property="og:title"', `<meta property="og:title" content="${escapeHtml(metadata.ogTitle)}" />`);
  html = updateMeta(html, 'property="og:description"', `<meta property="og:description" content="${escapeHtml(metadata.ogDescription)}" />`);
  if (metadata.ogUrl) html = updateMeta(html, 'property="og:url"', `<meta property="og:url" content="${metadata.ogUrl}" />`);
  else html = html.replace(/\s*<meta\s+property="og:url"[^>]*>/i, "");
  html = updateMeta(html, 'property="og:image"', `<meta property="og:image" content="${metadata.ogImage}" />`);
  html = updateMeta(html, 'name="twitter:title"', `<meta name="twitter:title" content="${escapeHtml(metadata.twitterTitle)}" />`);
  html = updateMeta(html, 'name="twitter:description"', `<meta name="twitter:description" content="${escapeHtml(metadata.twitterDescription)}" />`);
  html = updateMeta(html, 'name="twitter:image"', `<meta name="twitter:image" content="${metadata.twitterImage}" />`);
  if (metadata.canonical) html = html.replace(/<link\s+rel="canonical"[^>]*>/i, `<link rel="canonical" href="${metadata.canonical}" />`);
  else html = html.replace(/\s*<link\s+rel="canonical"[^>]*>/i, "");
  html = html.replace(/<script type="application\/ld\+json">[\s\S]*?<\/script>/i, `<script type="application/ld+json">${jsonLd}</script>`);
  const output = resolve(dist, route === "/" ? "index.html" : `${route.slice(1)}/index.html`);
  await mkdir(dirname(output), { recursive: true });
  await writeFile(output, html);
}

console.log(`Prerender SEO: ${getSeoRoutes().length} rutas generadas.`);
