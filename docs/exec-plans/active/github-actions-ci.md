# Exec Plan: GitHub Actions CI — Fase 4

Estado: IMPLEMENTACIÓN PUBLICADA / VALIDACIÓN GITHUB PENDIENTE

## Objetivo

Implementar la primera capa de integración continua de Turnelia para que una máquina limpia valide automáticamente backend y frontend en GitHub Actions ante cambios de código. Esta fase no incorpora Playwright ni modifica el comportamiento de la aplicación.

## Contexto y evidencia actual

- Fases 1A, 1B, 2 y 3 del Harness están completadas.
- La rama de trabajo actual es `feature/mvp`; existe también `main` y el remoto `origin`.
- Backend: Python/FastAPI, dependencias fijadas en `requirements.txt`, sin `pyproject.toml` ni `pytest.ini`.
- Frontend: npm con `frontend/package-lock.json` lockfile v3; scripts `test`, `lint` y `build`.
- Python local observado: 3.14.7. Node local observado: 24.19.0.
- `Dockerfile` usa Python 3.14-slim; el frontend usa Vite 8.
- Se creó y publicó `.github/workflows/ci.yml` en `feature/mvp` con la primera implementación del CI básico.
- Se intentó descubrir y ejecutar el workflow mediante `workflow_dispatch` sobre `feature/mvp`. GitHub respondió HTTP 404 porque el workflow todavía no está disponible en la rama por defecto `main`; no existe Run ID ni validación real de jobs.
- El bootstrap fue mergeado exclusivamente en `main` mediante el PR #1 (`8f10b983af884beb751911e96309f078f31bbf96`). GitHub reconoció el workflow y el run manual `32591912967` validó específicamente `feature/mvp`.
- Resultado real en `feature/mvp`: backend `536 passed, 26 skipped, 2 failed, 2 warnings`; frontend `168 passed, 3 failed` en `frontend/tests/excepcionesDisponibilidad.test.tsx`. El backend falló en dos pruebas del worker por configuración obligatoria ausente (`database_url`) y por una importación en subprocess sin `JWT_SECRET_KEY`; no se agregaron más variables ni se modificaron tests. Lint y build frontend no se ejecutaron después del fallo de Vitest.
- Corrección local posterior: `Base` fue separado de la conexión web para que la importación del worker no cargue `Settings()` ni requiera JWT; el test de `main()` aísla una configuración worker mínima; la suite de excepciones fija el reloj a `2026-08-22` y restaura timers. Validación dirigida: backend `14 passed`, frontend `11 passed`. Validación completa: backend `541 passed, 26 skipped, 2 warnings`; frontend `171 passed`; lint y build correctos. Aún no se ha ejecutado un nuevo run remoto de esta corrección.
- No existe evidencia local de branch protection ni de un pipeline CI ya operativo.

## Alcance

La implementación crea un workflow básico con dos jobs independientes:

1. `backend-ci`: checkout, Python compatible, cache de pip, instalación de `requirements.txt` y pytest.
2. `frontend-ci`: checkout, Node compatible, cache npm, `npm ci`, Vitest funcional, lint y build.

Los jobs deben producir estados independientes y fallar ante errores reales. Los comandos y el alcance Vitest quedan definidos más abajo para no incluir accidentalmente E2E.

## Fuera de alcance

- No ejecutar Playwright, Chromium, `verify.ps1 -E2E`, `e2e.ps1` ni Docker E2E.
- No crear branch protection en esta fase.
- No usar Aiven, Render, Mercado Pago, Resend, R2 ni ningún servicio productivo.
- No usar secretos productivos ni `DATABASE_URL` productiva.
- No corregir los tres fallos Vitest preexistentes como parte de este plan.
- No migrar a otro gestor, cambiar versiones sin evidencia o refactorizar código funcional.

## Arquitectura propuesta

Un workflow futuro, por ejemplo `.github/workflows/ci.yml`, correrá en `ubuntu-latest` con permisos mínimos (`contents: read`). Backend y frontend serán jobs separados para aislar fallos y permitir que cada ecosistema use su cache y comandos nativos.

### Triggers cerrados

- `pull_request` hacia `main`.
- `push` a `main`.
- `workflow_dispatch` para ejecución manual.

Mientras se trabaja en `feature/mvp` sin un PR abierto, `workflow_dispatch` permite ejecutar la validación manualmente sin ampliar los triggers automáticos de la primera versión.

### Versiones cerradas

- Python: `3.14`, alineado con `Dockerfile` y el runtime inspeccionado.
- Node: `24`, alineado con el runtime local observado y compatible con las dependencias actuales; `npm` será el incluido por la imagen/setup oficial.

El workflow usa esas versiones explícitamente y no contiene fallback silencioso. La disponibilidad efectiva en el runner de GitHub todavía debe validarse mediante una ejecución real posterior; si alguna action no puede resolverlas, la ejecución debe fallar y reportarlo.

## Backend CI y base de datos

La suite completa local observada terminó con `541 passed, 26 skipped`: las pruebas PostgreSQL se omiten si faltan variables específicas como `TEST_POSTGRES_*`; el fixture general de `tests/conftest.py` usa SQLite por defecto (`sqlite://`) y crea/descarta tablas por test.

Contrato definitivo de `backend-ci`: runner `ubuntu-latest`, checkout del repositorio, `actions/setup-python` con Python `3.14`, cache de pip dependiente de `requirements.txt`, `python -m pip install -r requirements.txt` y `python -m pytest`, ejecutado desde la raíz. La primera CI básica implementada no usa un servicio PostgreSQL. El resultado local de referencia es `541 passed, 26 skipped`; los skips deben permanecer visibles y no constituyen validación PostgreSQL completa. Las pruebas PostgreSQL selectivas requieren un trabajo futuro independiente con servicio, migraciones/fixtures controlados y variables `TEST_POSTGRES_*`; no se inventará una conexión común ni se usarán credenciales externas.

Comando exacto propuesto desde la raíz:

```bash
python -m pytest
```

La instalación será `python -m pip install -r requirements.txt`. No se ejecutarán migraciones ni seed en el job SQLite.

## Frontend CI y Vitest

Contrato definitivo de `frontend-ci`: runner `ubuntu-latest`, checkout del repositorio, working directory `frontend/`, `actions/setup-node` con Node `24`, cache npm dependiente de `frontend/package-lock.json`, `npm ci`, `npx vitest run tests`, `npm run lint` y `npm run build`. No incluye Playwright ni Chromium. La suite Vitest aislada se ejecutó con `npx vitest run tests`: `168 passed, 3 failed`, todos en `frontend/tests/excepcionesDisponibilidad.test.tsx`. La orden `npm test` sin alcance también descubre `frontend/e2e/*.spec.ts`, por lo que no es el comando canónico de CI.

El job implementado usa explícitamente el alcance Vitest unitario/frontend:

```bash
npx vitest run tests
```

No se usará `continue-on-error`, exclusiones, skips artificiales ni otra ocultación para los tres fallos. El job debe fallar ante el resultado real de Vitest; con el comportamiento normal de GitHub Actions, los pasos posteriores se detienen y no se usará `if: always` para simular un estado verde. Estos fallos no bloquean la implementación del workflow básico, pero sí impiden tratar `frontend-ci` como check obligatorio de branch protection hasta resolverlos o formalizar su tratamiento. No se corregirán en esta fase.

Comandos adicionales:

```bash
npm run lint
npm run build
```

## Relación con `verify.ps1`

Decisión cerrada: CI invocará comandos nativos, no `verify.ps1`. El runner inicial es Linux, mientras que `verify.ps1` contiene validaciones de entorno Windows, modos locales y E2E; reutilizarlo introduciría una capa PowerShell no necesaria y podría mezclar Quick/Full/E2E. Los comandos CI deben permanecer explícitos y equivalentes al alcance backend/frontend definido aquí.

`verify.ps1 -Full` seguirá siendo la validación local del Harness en Windows. CI será una validación independiente sobre una máquina Linux limpia, con comandos nativos y el alcance explícito definido aquí; no son ejecuciones idénticas ni una invoca a la otra.

## Cache

- Backend: cache de pip mediante `actions/setup-python` con `cache: pip` y `requirements.txt` como dependencia de cache.
- Frontend: `actions/setup-node` con `cache: npm` y `cache-dependency-path: frontend/package-lock.json`.
- Siempre ejecutar `npm ci`; no usar `npm install` como fallback.

La cache es una optimización, no una fuente de verdad. Un fallo de cache debe permitir una instalación limpia.

## Variables, servicios y secretos

El job básico no requiere variables secretas, `DATABASE_URL`, PostgreSQL, Docker ni servicios externos. Debe fijar sólo valores locales/no sensibles si algún import los exige, sin imprimirlos. No se deben copiar `.env`, backups ni credenciales al runner.

Permisos mínimos del workflow: `contents: read`. No usar tokens personalizados, ambientes productivos, API keys, credenciales de Render/Aiven o secretos de Mercado Pago, Resend o R2. Los logs no deben incluir secretos ni connection strings.

## Fallos, artefactos y timeout

- Un comando fallido hace fallar su job y el workflow.
- Timeout global sugerido: 15 minutos; cada job podrá tener un límite menor si la medición inicial lo permite.
- La primera versión no subirá artefactos: se usarán los logs estándar de GitHub Actions.
- Si se agregan logs de diagnóstico, deben ser sanitizados y limitarse a fallos del job.
- No subir `node_modules`, `.venv`, coverage, `.env`, dumps, storage state ni artefactos Playwright.

## E2E futuro

Playwright queda fuera de esta primera implementación CI. Se documentará como Fase 4B / CI E2E futura, con Docker E2E aislado, variables locales/sintéticas, Chromium explícito y cleanup seguro. No se instalará Chromium en el CI básico ni se reutilizará `DATABASE_URL` productiva.

## Branch protection futura

No se implementará ahora. En una etapa posterior `backend-ci` podrá ser requerido cuando el CI esté validado; `frontend-ci` sólo podrá ser requerido cuando Vitest esté consistentemente verde. Mientras existan los tres fallos actuales, no se declararán checks obligatorios.

## Decisiones abiertas

No quedan decisiones funcionales abiertas que bloqueen la implementación del CI básico. Permanecen como trabajo futuro no bloqueante:

1. Diseñar un job independiente para PostgreSQL CI selectivo.
2. Diseñar la Fase 4B para Playwright/Chromium.
3. Definir posteriormente artefactos o cobertura si aportan diagnóstico.
4. Configurar branch protection cuando se cumplan las condiciones indicadas arriba, incluyendo el tratamiento formal de los tres fallos Vitest.

La disponibilidad de Python 3.14 y Node 24 en las actions oficiales es una precondición mecánica que debe verificarse durante la implementación, no una decisión funcional pendiente.

## Pasos de implementación

1. Verificar en GitHub Actions que las actions oficiales resuelven Python 3.14 y Node 24.
2. Ejecutar el workflow en PR/push o mediante dispatch y revisar estados independientes, tiempos y logs sanitizados.
3. Mantener la documentación actualizada después de observar una ejecución real.

## Validación del plan

En esta fase se realizaron diagnósticos locales: pytest completo y Vitest con alcance `tests`, además de lint y build frontend. El workflow fue revisado localmente por estructura, triggers, permisos, caches, working directories y ausencia de servicios/secretos fuera de alcance. Tras el merge exclusivo del bootstrap en `main`, el run `32591912967` ejecutó GitHub Actions sobre `feature/mvp`. Python `3.14.7`, Node `24.19.0` y `npm ci` fueron correctos; los fallos reales descritos arriba mantienen la Fase 4 en curso.

## Rollback

Antes de activar el workflow obligatorio, eliminar o revertir únicamente el archivo `.github/workflows/ci.yml` mediante un commit autorizado. No tocar código funcional, datos, producción ni configuraciones externas. Si un job resulta inestable, desactivar temporalmente la exigencia de branch protection futura, sin ocultar fallos del workflow.

## Riesgos

- Python 3.14 o Node 24 podrían no estar disponibles en la imagen/action elegida al momento de implementar.
- El job SQLite no demuestra compatibilidad PostgreSQL; los 26 skips deben seguir visibles.
- `npm test` descubre E2E; usar el alcance explícito evita mezclar suites, pero requiere documentarlo.
- Los tres fallos Vitest impedirían un CI frontend obligatorio si no se resuelven.
- Cambios futuros en actions, runners o lockfiles pueden alterar tiempos y compatibilidad.

## Criterios de aceptación

- Existe `.github/workflows/ci.yml`, revisado localmente, sin Playwright ni Chromium.
- PR a `main`, push a `main` y ejecución manual ejecutan backend y frontend en jobs separados; no se añade push automático a `feature/mvp`.
- Backend instala requirements y ejecuta pytest; skips PostgreSQL son visibles.
- Frontend ejecuta sólo Vitest unitario/frontend con alcance explícito, lint y build.
- No se usan servicios productivos, secretos ni `DATABASE_URL` productiva.
- Los fallos reales producen estado fallido; no existe `continue-on-error` para Vitest.
- La documentación refleja el resultado real y mantiene Fase 4 diferenciada de Fase 4B E2E.
