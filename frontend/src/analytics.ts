type Gtag = (...args: unknown[]) => void;
declare global { interface Window { dataLayer?: unknown[]; gtag?: Gtag; } }
const MEASUREMENT_ID = "G-7Y07NRSBZE";
const EVENTOS_PERMITIDOS = new Set(["sign_up_click", "sign_up_start", "sign_up_complete", "login_success", "subscription_start", "subscription_complete"]);
const RUTAS_PUBLICAS = ["/", "/login", "/registro", "/ayuda"];
let inicializando: Promise<void> | undefined;
export function esRutaPublica(path: string): boolean { return RUTAS_PUBLICAS.includes(path) || path.startsWith("/ayuda/"); }
function cargarAnalytics(): Promise<void> {
  if (!import.meta.env.PROD || window.gtag) return Promise.resolve();
  if (inicializando) return inicializando;
  inicializando = new Promise((resolve) => {
    window.dataLayer = window.dataLayer || [];
    window.gtag = (...args: unknown[]) => window.dataLayer?.push(args);
    window.gtag("js", new Date());
    window.gtag("config", MEASUREMENT_ID, { send_page_view: false });
    const script = document.createElement("script"); script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${MEASUREMENT_ID}`;
    script.onload = () => resolve(); script.onerror = () => resolve(); document.head.append(script);
  });
  return inicializando;
}
export function trackEvent(name: string, params?: Record<string, string>): void {
  if (!EVENTOS_PERMITIDOS.has(name)) return;
  const parametrosSeguros = params ? Object.fromEntries(Object.entries(params).filter(([key]) => key === "source" || key === "plan")) : undefined;
  void cargarAnalytics().then(() => window.gtag?.("event", name, parametrosSeguros ?? {}));
}
export function trackPageView(path: string): void {
  if (!esRutaPublica(path)) return;
  void cargarAnalytics().then(() => window.gtag?.("event", "page_view", { page_path: path }));
}
