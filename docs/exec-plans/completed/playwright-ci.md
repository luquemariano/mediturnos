# Exec Plan: Playwright E2E CI

Estado: COMPLETADO

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

- [x] Job `Playwright E2E CI` ejecutable por `workflow_dispatch`.
- [x] PostgreSQL, Alembic, seed, API y frontend listos.
- [x] Chromium instalado y las tres specs verdes.
- [x] Cleanup seguro y artifacts sólo ante fallo.
- [x] Sin secretos productivos ni providers externos.
- [x] Reviewer aprueba la implementación y validación.

## Progreso

- [x] Contratos locales inspeccionados.
- [x] Job y variables sintéticas implementados.
- [x] Readiness, sanitización, cleanup y artifacts definidos.
- [x] Validación remota: run `32598856151`, commit `a2124ff895797708097abee5cdf7514b82932990`, resultado `success`.
- [x] Backend CI, PostgreSQL CI, Frontend CI y Playwright E2E CI verdes.
- [x] Playwright: `3 passed (4.2s)` en `smoke.spec.ts`, `auth.spec.ts` y `admin.spec.ts`.
- [x] Cleanup E2E completado; upload de logs omitido por ejecución exitosa.
- [x] Revisión del Reviewer: Fase 7A aprobada para cierre.

## Evidencia remota Fase 7A

La ejecución manual mediante `workflow_dispatch` sobre `feature/mvp` fue
exitosa. El job instaló Chromium, inició PostgreSQL E2E, aplicó Alembic,
cargó el seed sintético, verificó API y frontend, y ejecutó las tres specs
con `3 passed (4.2s)`. El cleanup eliminó exclusivamente los recursos
Compose `turnelia-e2e` y no publicó artifacts porque no hubo fallo.

El mismo run dejó verdes `Backend CI`, `PostgreSQL CI` y `Frontend CI`. El
Ruleset no fue modificado y `Playwright E2E CI` continúa siendo informativo,
no required. Las fases 7B y 7C permanecen fuera de alcance.
