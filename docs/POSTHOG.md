# PostHog

Turnelia usa PostHog para Product Analytics, Web Analytics y Session Replay en la región EU (`https://eu.i.posthog.com`). La integración es independiente de GA4, que conserva su funcionamiento actual.

PH1.1 inicializa PostHog sólo en builds productivos con `VITE_POSTHOG_PROJECT_TOKEN` y `VITE_POSTHOG_HOST`. Autocapture está deshabilitado y no se agregan eventos de negocio; la wrapper mantiene una allowlist vacía para fases posteriores.

La privacidad está configurada estrictamente: se enmascara todo texto y atributo DOM, todos los inputs, y se bloquean inputs, textareas, selects y contenido editable en replay. No se llama `identify`. Las variables `VITE_*` deben estar disponibles durante el build; no se incluyen valores reales en el repositorio.
