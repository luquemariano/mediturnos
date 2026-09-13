export function buildPublicBookingUrl(slug: string, baseUrl = window.location.origin): string {
  return `${baseUrl.replace(/\/$/, "")}/reservar/${encodeURIComponent(slug)}`;
}
