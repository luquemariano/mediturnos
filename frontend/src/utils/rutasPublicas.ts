const RUTAS_PUBLICAS_EXACTAS = new Set([
  "/",
  "/ayuda",
  "/estudios/enviar",
  "/suscripcion/retorno",
  "/login",
  "/registro",
  "/forgot-password",
  "/reset-password",
]);

export function esRutaPublica(pathname: string): boolean {
  return RUTAS_PUBLICAS_EXACTAS.has(pathname) || pathname.startsWith("/ayuda/");
}

export function debeForzarOnboarding(pathname: string): boolean {
  return !esRutaPublica(pathname) && !pathname.startsWith("/onboarding/");
}
