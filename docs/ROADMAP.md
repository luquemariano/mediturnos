# Roadmap de Turnelia

Estados: **PENDIENTE**, **EN CURSO**, **COMPLETADO** y **NO DETERMINADO**. No se asignan fechas ni prioridades comerciales no documentadas.

## Producto

- **PENDIENTE:** calendario semanal/mensual, según la evolución descrita en README.
- **PENDIENTE:** auditoría de cambios, mencionada como evolución posible.
- **PENDIENTE:** verificación operativa de pagos y notificaciones en producción.
- Estrategia comercial, precios y prioridades: **NO DETERMINADOS**.

## Ingeniería

- **COMPLETADO:** Playwright y flujos E2E; smoke, login/logout administrativo y navegación a `CuentasAdmin` validados con PostgreSQL E2E aislado en Docker. El modo headed es opcional y la validación real fue aprobada.
- **PENDIENTE:** ampliar validación PostgreSQL más allá de suites selectivas.
- **PENDIENTE:** observabilidad operativa verificable.
- **PENDIENTE:** normalización controlada MediTurnos → Turnelia.
- **PENDIENTE:** estrategia formal de ramas y rollback; detalles actuales **NO DETERMINADOS**.
- **COMPLETADO:** primera capa documental de arquitectura, producto, estado, decisiones y workflow.

## Harness

- **COMPLETADO:** Fase 1A, memoria canónica inicial.
- **COMPLETADO:** Fase 1B, incluyendo `SECURITY.md`, `TESTING.md`, `DEPLOYMENT.md`, `ROADMAP.md` y la estructura de Exec Plans.
- **COMPLETADA:** Fase 2 setup/verify; `setup.ps1` y `verify.ps1` están implementados y el Exec Plan fue completado. Full detecta actualmente tres fallos Vitest preexistentes en `frontend/tests/excepcionesDisponibilidad.test.tsx`; no bloquean el Harness.
- **COMPLETADA:** Fase 3 Playwright/E2E; entorno aislado, fixture sintético, `e2e.ps1`, `setup.ps1 -E2E`, `verify.ps1 -E2E` y 3 tests validados.
- **COMPLETADO:** flujo Builder → Reviewer documentado manualmente.
- **NO INCORPORADAS:** Skills específicas.
- **NO INCORPORADO:** MCP.
- **NO INCORPORADOS:** multiagentes automatizados.
- **PENDIENTE:** template SaaS.
- **EN CURSO:** Fase 4 GitHub Actions CI; el bootstrap mínimo fue mergeado en `main` y `workflow_dispatch` validó `feature/mvp` en el run `32591912967`. La corrección local del aislamiento worker y de las fechas frontend dejó backend en `541 passed, 26 skipped` y frontend en `171 passed`; lint y build también pasan. La validación remota posterior y el tratamiento de los warnings/fallos históricos de CI quedan pendientes; el diseño y resultados quedan documentados en [`github-actions-ci.md`](exec-plans/active/github-actions-ci.md).
