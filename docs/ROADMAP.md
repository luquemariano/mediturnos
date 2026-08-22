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
- **COMPLETADA:** Fase 4 GitHub Actions CI; el bootstrap fue mergeado en `main` y la validación remota final de `feature/mvp` (`32592968005`, commit `1985d22`) pasó en backend y frontend. Backend: `538 passed, 26 skipped, 2 warnings`; frontend: `171 passed`; lint y build correctos. El plan completado queda en [`github-actions-ci.md`](exec-plans/completed/github-actions-ci.md).
- **COMPLETADA:** Fase 5 protección de `main`; Ruleset activo con PR obligatorio, `Backend CI` y `Frontend CI` requeridos, 0 aprobaciones, `up-to-date` no obligatorio y force-push/eliminación bloqueados. PR #2: checks fallidos → merge bloqueado. PR #3: run `32595185386`, ambos checks `success` → merge permitido; fue cerrado sin merge y sin bypass. PostgreSQL CI quedó fuera del alcance de Fase 5; Playwright CI, branch protection avanzada futura, aprobaciones humanas y `up-to-date` obligatorio siguen fuera de alcance.
- **COMPLETADA:** Fase 6 PostgreSQL CI; job separado con PostgreSQL `17-alpine`, Alembic y tres módulos PostgreSQL seleccionados. Run `32597419679` verde (`23 passed, 0 failed, 0 skipped`). PostgreSQL CI quedó required en el Ruleset `Turnelia main protection`; el PR #4 confirmó los tres checks verdes y merge permitido, sin mergear.
- **IMPLEMENTADA / PENDIENTE DE REVIEWER:** Fase 7A Playwright E2E CI; job separado informativo, sólo `workflow_dispatch`, PostgreSQL E2E, Chromium headless, smoke/auth/admin y artifacts limitados a logs sanitizados ante fallo. Run `32598856151` sobre `a2124ff`: `3 passed (4.2s)`, cleanup correcto. Fases 7B y 7C quedan pendientes.
