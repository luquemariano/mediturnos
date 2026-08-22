# Exec Plan: Playwright E2E CI

Estado: EN CURSO

## Objetivo y alcance

Implementar en Fase 7A un job remoto separado `Playwright E2E CI`, ejecutable
únicamente mediante `workflow_dispatch`, informativo y no required. Las fases
7B (PR informativo y observación de estabilidad) y 7C (evaluación de required
y cambio del Ruleset) quedan fuera de alcance.

## Arquitectura

El job usa `ubuntu-latest`, Python 3.14, Node 24, `npm ci`, Chromium instalado
con `npx playwright install --with-deps chromium` y el Compose E2E existente
`turnelia-e2e`, limitado al PostgreSQL local en `127.0.0.1:55432`. Ejecuta
Alembic, el seed sintético, API en `127.0.0.1:8001`, Vite en
`127.0.0.1:5174` y Chromium headless con workers 1, retries 0 y video off.

## Variables

El job define sólo valores sintéticos para `E2E_DB_PASSWORD`, `DATABASE_URL`,
`E2E_JWT_SECRET`, `JWT_SECRET_KEY`, `APP_ENV`, `E2E_DATABASE_NAME`,
`E2E_ADMIN_PASSWORD`, `VITE_API_URL`, `CORS_ALLOWED_ORIGINS`, `FRONTEND_URL`,
`EMAIL_PROVIDER` y `OBJECT_STORAGE_PROVIDER`. No usa `.env`, GitHub Secrets
productivos ni fallback a producción.

## Readiness y datos

PostgreSQL se valida mediante `pg_isready`; las migraciones usan únicamente la
URL E2E y el seed crea datos sintéticos. API y frontend se sondean por HTTP con
timeout de 60 segundos y detección temprana de procesos muertos. No se usan
sleeps fijos como sustituto de readiness.

## Artifacts y seguridad

Ante fallo sólo pueden publicarse `api.log`, `frontend.log` y `postgres.log`,
sanitizados y con retención máxima de 7 días. No se publican traces,
screenshots, HTML reports, cookies, localStorage, headers, JWT, passwords,
`.env` ni connection strings. Los PID son temporales y no se suben.

El cleanup captura y sanitiza logs, detiene grupos de API/frontend por PID,
ejecuta `docker compose -p turnelia-e2e ... down -v --remove-orphans` y elimina
temporales. No usa `killall`.

## Riesgos y fases posteriores

Persisten riesgos de exposición accidental en logs, procesos huérfanos,
diferencias entre desarrollo y producción, coste de Chromium y cambios futuros
de variables. PostgreSQL externo, Aiven, Render, Mercado Pago, Resend y R2 no
se utilizan. El Ruleset no se modifica.

## Criterios de aceptación

- [ ] Job `Playwright E2E CI` ejecutable por `workflow_dispatch`.
- [ ] PostgreSQL, Alembic, seed, API y frontend listos.
- [ ] Chromium instalado y las tres specs verdes.
- [ ] Cleanup seguro y artifacts sólo ante fallo.
- [ ] Sin secretos ni providers externos.
- [ ] Reviewer aprueba la implementación y validación.

## Progreso

- [x] Contratos locales inspeccionados.
- [x] Job y variables sintéticas implementados.
- [x] Readiness, sanitización, cleanup y artifacts definidos.
- [ ] Validación local y remota.
- [ ] Revisión del Reviewer.
