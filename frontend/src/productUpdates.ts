export type ProductUpdate = {
  id: string;
  title: string;
  description: string;
  publishedAt: string;
  ctaLabel: string;
  ctaPath: string;
  helpPath: string;
  badge: string;
  active: boolean;
};

export const PRODUCT_UPDATES: ProductUpdate[] = [{
  id: "f12-7-waitlist-discovery",
  title: "Nuevo: Lista de espera inteligente",
  description: "Recuperá turnos cancelados ofreciendo automáticamente el horario a pacientes que están esperando.",
  publishedAt: "2026-09-13",
  ctaLabel: "Probar lista de espera",
  ctaPath: "/lista-espera",
  helpPath: "/ayuda/lista-de-espera",
  badge: "Nuevo",
  active: true,
}];

export function getLatestActiveProductUpdate(updates: ProductUpdate[] = PRODUCT_UPDATES): ProductUpdate | undefined {
  return updates.filter((update) => update.active).sort((a, b) => b.publishedAt.localeCompare(a.publishedAt))[0];
}

export const ACTIVE_PRODUCT_UPDATE = getLatestActiveProductUpdate();
