# Exec Plan: Playwright E2E CI — Fase 7B

Estado: COMPLETADO

## Objetivo

Habilitar `Playwright E2E CI` automáticamente en Pull Requests hacia `main`,
manteniéndolo informativo y no required. `workflow_dispatch` se conserva como
fallback manual. Fase 7C, estabilidad prolongada y eventual required quedan
fuera de alcance.

## Contrato

- Trigger: `pull_request` hacia `main` y `workflow_dispatch`.
- Sin `push` específico a `feature/mvp`.
- Sin `pull_request_target` ni filtros por paths.
- El job conserva PostgreSQL E2E, Alembic, seed sintético, API, frontend,
  Chromium y las tres specs de 7A.
- La concurrencia sólo agrupa `Playwright E2E CI` por PR o ref y cancela
  ejecuciones obsoletas del mismo contexto.
- `contents: read`; no se usan servicios externos ni secretos productivos.
- Artifacts: sólo logs sanitizados ante fallo; sin traces, screenshots o HTML.

## Estado de required

Playwright E2E CI no es required. El Ruleset permanece sin cambios y conserva
únicamente los checks ya establecidos. La evaluación de required corresponde a
Fase 7C.

## Criterios de aceptación

- [x] Pull Request hacia `main` ejecuta los cuatro jobs.
- [x] `workflow_dispatch` continúa funcionando.
- [x] Playwright es informativo y no bloquea por Ruleset.
- [ ] Cinco ejecuciones verdes, en al menos tres PRs o actualizaciones,
  sin flakiness no explicada ni skips inesperados.
- [x] Reviewer aprueba la implementación y validación de 7B para cierre.

La estabilidad acumulada requerida para evaluar Fase 7C sigue pendiente: aún
se necesitan cinco ejecuciones verdes, al menos tres PRs o actualizaciones,
cero flakiness no explicada, cleanup y readiness estables, y ningún skip
inesperado.

## Evidencia inicial

El commit de implementación `3cfcf77` fue publicado en `feature/mvp` y el
`workflow_dispatch` `32599865574` terminó correctamente con cuatro jobs
verdes y `3 passed (4.8s)` en Playwright.

El PR controlado #5 hacia `main`, con head SHA `3cfcf77`, no generó checks
porque tenía conflicto de merge. Fue cerrado sin merge y la rama temporal fue
eliminada; esto no fue un fallo de Playwright ni del trigger.

La validación reconciliada se realizó en el PR #6, con head SHA `cb28183` y
base SHA `8f10b983af884beb751911e96309f078f31bbf96`. GitHub generó el run
`32600285274` con evento `pull_request`; el PR fue `MERGEABLE/CLEAN` y los
cuatro jobs terminaron en `success`. Playwright completó PostgreSQL E2E,
Alembic, seed, API/frontend readiness, Chromium y las tres specs con
`3 passed (4.7s)`. El cleanup fue correcto y el PR se cerró sin merge.

Estado de concurrencia: CONFIGURADA / NO VALIDADA EMPÍRICAMENTE; no se forzó
una cancelación artificial.
