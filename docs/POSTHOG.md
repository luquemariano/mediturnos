# PostHog

Turnelia usa PostHog para Product Analytics, Web Analytics y Session Replay en la región EU (`https://eu.i.posthog.com`). La integración es independiente de GA4, que conserva su funcionamiento actual.

PH2.1 agrega Product Analytics mediante eventos explícitos y una allowlist estricta de eventos y propiedades. Se instrumentan altas, verificación de email, login, onboarding, creación de prestaciones/disponibilidades/pacientes/turnos y acciones de reserva pública. No se instrumentan evoluciones clínicas, estudios, documentos, cambios de perfil ni reprogramaciones/cancelaciones internas cuando no hay un punto seguro común identificado.

La wrapper elimina propiedades desconocidas, PII, objetos y arrays; además normaliza errores públicos a `validation`, `conflict`, `rate_limit`, `network`, `server` o `unknown`. No se llama `identify`.

La privacidad está configurada estrictamente: se enmascara todo texto y atributo DOM, todos los inputs, y se bloquean inputs, textareas, selects y contenido editable en replay. No se llama `identify`. Las variables `VITE_*` deben estar disponibles durante el build; no se incluyen valores reales en el repositorio.
