# Estado actual de Turnelia

Fecha de referencia: **2026-08-22**. Es una fotografía del repositorio, no una certificación operativa de producción.

## Convención de estados

- **IMPLEMENTADO EN CÓDIGO:** existe código y, cuando corresponde, tests.
- **DECLARADO EN CONFIGURACIÓN:** aparece en configuración de deployment o entorno, sin verificar ejecución real.
- **VERIFICADO EN PRODUCCIÓN:** comprobado mediante evidencia operativa de producción; no se asigna sin esa evidencia.
- **NO DETERMINADO:** el repositorio no permite concluir el estado.
- **NO INCORPORADO:** capacidad prevista o mencionada que todavía no existe en el repositorio.
- **LEGACY:** referencia histórica o técnica que no representa necesariamente el producto actual.

| Área | Estado | Evidencia/límite |
|---|---|---|
| Landing, autenticación, profesionales, pacientes | IMPLEMENTADO EN CÓDIGO | Código, componentes y tests |
| Especialidades, prestaciones, disponibilidad, turnos | IMPLEMENTADO EN CÓDIGO | Routers, servicios, modelos y tests |
| Pagos clínicos, suscripciones SaaS | IMPLEMENTADO EN CÓDIGO | Servicios, webhooks y tests |
| Evoluciones, perfiles clínicos, documentos | IMPLEMENTADO EN CÓDIGO | Modelos, endpoints y tests |
| Solicitudes y carga pública de estudios | IMPLEMENTADO EN CÓDIGO | Flujos tokenizados y tests |
| Notificaciones, recordatorios y email | IMPLEMENTADO EN CÓDIGO | Servicios, worker, Resend/in-memory |
| R2 | DECLARADO EN CONFIGURACIÓN | Adaptador R2 y fake; uso real NO DETERMINADO |
| Deployment Render | DECLARADO EN CONFIGURACIÓN | Blueprint declarado; ejecución real NO DETERMINADA |
| PostgreSQL de producción | DECLARADO EN CONFIGURACIÓN | Proveedor/ubicación documentados: Aiven; conexión y salud actuales NO DETERMINADAS |
| E2E / Playwright | NO INCORPORADO | No hay suite, dependencia ni configuración; queda como capacidad futura |
| Documentación Harness | IMPLEMENTADO EN CÓDIGO | AGENTS y documentos de esta fase |

## Snapshot Git de la inspección

- Rama: `feature/mvp`.
- HEAD: `be5068a feat: improve clinical study review experience and notifications`.
- Snapshot tomado el 2026-08-22 mediante `git status --short`, `git log -1` y `git rev-list --left-right --count main...HEAD`.
- En ese snapshot, la rama estaba 85 commits adelante y 0 atrás de `main`.
- También aparecían `.vscode/`, `scripts/` y `tests/test_debug_preapproval_payload.py` como no trackeados. Este dato es histórico del snapshot, no una verdad permanente.

## Interpretación

La presencia de código/configuración/tests demuestra **IMPLEMENTADO EN CÓDIGO**. La configuración de Render/R2/cron demuestra **DECLARADO EN CONFIGURACIÓN**. La ubicación/proveedor productivo documentado para PostgreSQL es Aiven, según la historia operativa del proyecto y no como inferencia de `render.yaml`. No hay evidencia suficiente para marcar componentes como **VERIFICADO EN PRODUCCIÓN**; estado actual de Render, conexión/salud de PostgreSQL, cron, email, R2 y Mercado Pago: **NO DETERMINADO**.

## Deuda y riesgos

Conviven MediTurnos/Turnelia en branding, nombres técnicos, emails de prueba y servicios Render. También existen dos familias de variables Mercado Pago. SQLite no sustituye una validación PostgreSQL completa y no hay Playwright.
