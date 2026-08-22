# Decisiones registradas

Registro ligero de decisiones demostrables y revisables.

## DEC-001 — PostgreSQL como base productiva

Tipo: convención vigente del sistema. No se conoce el razonamiento histórico original.

`docker-compose.yml`, `render.yaml` y `app/database/connection.py` muestran PostgreSQL para producción/deployment y SQLite principalmente para tests. Los cambios deben preservar PostgreSQL.

## DEC-002 — Alembic para cambios persistentes

Tipo: restricción arquitectónica actual.

El esquema evoluciona mediante `alembic/versions/`; `app.scripts.start` aplica `alembic upgrade head` antes de iniciar la API.

## DEC-003 — React, TypeScript y Vite

Tipo: stack actual derivado de implementación.

`frontend/package.json` y `frontend/src/` establecen el stack. El routing manual actual no debe describirse como React Router.

## DEC-004 — JWT para sesión

Tipo: mecanismo actual derivado de implementación.

La API usa Bearer JWT y el frontend conserva `access_token` en `localStorage`, con controles de rol y ownership.

## DEC-005 — Render como deployment declarado

Tipo: deployment declarado en configuración; operación real NO DETERMINADA.

`render.yaml` declara API Docker, Static Site y Cron, con health check `/health/ready`.

## DEC-006 — Abstracción de email

Tipo: convención vigente derivada de implementación; entrega real NO DETERMINADA.

El código soporta proveedor `in_memory` para entornos controlados y Resend para el deployment declarado. Entrega real NO DETERMINADA.

## DEC-007 — Storage configurable

Tipo: capacidad actual derivada de implementación; uso productivo NO DETERMINADO.

Existe una abstracción con R2 y fake en `app/integrations/storage/`; el uso productivo de R2 es NO DETERMINADO.

## DEC-008 — Recordatorios mediante worker/cron

Tipo: comportamiento implementado y deployment declarado; ejecución real NO DETERMINADA.

`app.scripts.process_appointment_reminders` está declarado en Render cada 15 minutos; su ejecución real NO DETERMINADA.

## DEC-009 — Pagos clínicos y suscripciones SaaS separados

Tipo: restricción arquitectónica actual derivada de implementación.

Servicios, variables, modelos, endpoints y tests distinguen ambos flujos Mercado Pago.

## DEC-010 — Preservación de naming histórico

Tipo: convención vigente de compatibilidad.

Turnelia es la marca; `mediturnos`/`MediTurnos` se conserva donde es identificador técnico o histórico. Cualquier renombrado requiere tarea controlada.

## DEC-011 — Protección de la rama `main`

Tipo: control de repositorio verificado en GitHub; Fase 5 cerrada.

El repositorio utiliza el Ruleset activo `Turnelia main protection`, dirigido
únicamente a `refs/heads/main`. Exige Pull Request y los checks `Backend CI` y
`Frontend CI`, con cero aprobaciones obligatorias y sin exigir actualización
estricta de la rama. Bloquea force-push y eliminación de `main`. El bypass
administrativo está limitado a Pull Requests. No incluye PostgreSQL CI,
Playwright CI ni gates de deployment. El fallback Classic queda documentado
en el Exec Plan. La validación roja del PR #2 confirmó el bloqueo y la
validación verde del PR #3, run
`32595185386`, terminó `CLEAN`/`MERGEABLE` sin bypass; el PR fue cerrado sin
merge. Estado final: Fase 5 cerrada.

## DEC-012 — PostgreSQL CI requerido

Tipo: decisión de Harness implementada y validada remotamente.

PostgreSQL CI se ejecuta como job separado con `postgres:17-alpine`, variables
sintéticas, Alembic y tres módulos PostgreSQL seleccionados. Se ejecuta
secuencialmente y verifica mediante JUnit que ningún módulo obligatorio quede
completamente skipped. El Ruleset `Turnelia main protection` lo exige junto a
`Backend CI` y `Frontend CI`. El PR #4, run `32597812092`, confirmó los tres
checks verdes y merge permitido sin bypass; el PR fue cerrado sin merge.

## DEC-013 — Playwright E2E CI informativo

Tipo: decisión de Harness implementada, validada remotamente y aprobada para
cierre por el Reviewer.

Fase 7A usa un job separado `Playwright E2E CI`, ejecutable sólo mediante
`workflow_dispatch`, con PostgreSQL E2E local, Chromium headless y datos
sintéticos. No se habilita trigger de PR, no se modifica el Ruleset y no se
publican traces, screenshots ni HTML reports; ante fallo sólo se permiten logs
sanitizados de API, frontend y PostgreSQL. Las fases 7B y 7C son posteriores.

La validación manual sobre `feature/mvp` quedó registrada en el run
`32598856151`, commit `a2124ff`: Chromium, PostgreSQL E2E, Alembic, seed,
API y frontend completaron correctamente; las tres specs produjeron
`3 passed (4.2s)`. El cleanup fue correcto y no se subieron logs al no haber
fallo. Playwright CI sigue siendo informativo y no required.

Para Fase 7B se habilita el job también en `pull_request` hacia `main`, sin
`pull_request_target`, sin filtros de paths y conservando `workflow_dispatch`.
La concurrencia se limita al job Playwright y cancela sólo ejecuciones
obsoletas del mismo PR. El Ruleset permanece sin cambios; la evaluación de
required queda reservada para Fase 7C.
