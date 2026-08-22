# Exec Plan: Playwright E2E CI — Fase 7B

Estado: EN CURSO

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

- [ ] Pull Request hacia `main` ejecuta los cuatro jobs.
- [ ] `workflow_dispatch` continúa funcionando.
- [ ] Playwright es informativo y no bloquea por Ruleset.
- [ ] Cinco ejecuciones verdes, en al menos tres PRs o actualizaciones,
  sin flakiness no explicada ni skips inesperados.
- [ ] Reviewer aprueba la estabilidad de 7B.
