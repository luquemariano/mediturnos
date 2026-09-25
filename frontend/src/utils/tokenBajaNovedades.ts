export function extraerYLimpiarTokenBaja(): string | null {
  if (window.location.pathname !== "/baja-novedades") return null;

  const url = new URL(window.location.href);
  const token = url.hash.length > 1 ? url.hash.slice(1) : null;
  url.hash = "";
  url.searchParams.delete("token");
  window.history.replaceState(window.history.state, "", `${url.pathname}${url.search}`);
  return token;
}
