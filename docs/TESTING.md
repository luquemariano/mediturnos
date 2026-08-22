# Testing de Turnelia

Fuente canónica para validar cambios. No se declaran porcentajes de cobertura porque no están disponibles.

## Backend

Ubicación: `tests/`.

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Este comando depende de que exista el entorno virtual local `.venv` con las dependencias instaladas. Como alternativa genérica, cuando Python y las dependencias estén disponibles en el entorno activo, puede ejecutarse:

```powershell
python -m pytest
```

Ninguna de las dos formas es universalmente superior: la primera usa explícitamente el entorno virtual del repositorio y la segunda depende de la configuración activa del entorno.

`tests/conftest.py` contiene fixtures compartidos. La mayoría de pruebas usa SQLite, incluidas bases in-memory. Hay suites PostgreSQL selectivas para concurrencia, pagos, recordatorios y acciones relacionadas.

La colección cubre autenticación, recuperación, roles/ownership, profesionales, pacientes, turnos, disponibilidad, excepciones, feriados, solapamientos, concurrencia, pagos, webhooks, suscripciones, recordatorios, emails, documentos, estudios, evoluciones, perfiles clínicos, notificaciones, storage, rate limiting, health checks, seed y bootstrap.

La profundidad de cobertura varía por módulo. Consultar `tests/` para el detalle. Sólo algunos flujos cuentan con validación PostgreSQL explícita.

## Frontend

Ubicación: `frontend/tests/`. Usa Vitest, Testing Library, jsdom, TypeScript y Vite.

```powershell
Set-Location frontend
npm test
npm run lint
npm run build
```

Hay cobertura de sesión, recuperación, dashboards, agenda, pacientes, profesionales, disponibilidad, prestaciones, suscripciones, estudios, documentos, notificaciones y SEO.

La cobertura no es uniforme entre módulos. Consultar `frontend/tests/` para el detalle.

## Limitaciones actuales

- Playwright está configurado para Chromium y la suite MVP vive en `frontend/e2e/`.
- La ejecución E2E requiere Docker, Chromium instalado y el entorno aislado que prepara `e2e.ps1`.
- SQLite no demuestra compatibilidad PostgreSQL total.
- Tests locales no validan la operación productiva de Render, Aiven, Resend, R2 o Mercado Pago.
- La cobertura PostgreSQL es selectiva.

## Verificación del Harness

Desde la raíz del repositorio:

```powershell
powershell -ExecutionPolicy Bypass -File .\verify.ps1 -Quick
powershell -ExecutionPolicy Bypass -File .\verify.ps1 -Full
```

Quick no ejecuta las suites completas. Full ejecuta pytest backend, Vitest frontend, lint y build; los servicios locales sólo se comprueban con `-LocalServices`. `-LocalServices` es read-only: comprueba Docker, el servicio Compose `db`, `127.0.0.1:5432` y `http://127.0.0.1:8000/health/ready`, sin iniciar servicios ni contactar producción. En la validación de Fase 2, Quick pasó; pytest, lint y build pasaron; Vitest presentó tres fallos en `frontend/tests/excepcionesDisponibilidad.test.tsx`.
Quick no ejecuta las suites completas. Full ejecuta pytest backend, Vitest frontend, lint y build; los servicios locales sólo se comprueban con `-LocalServices`. `-LocalServices` es read-only: comprueba Docker, el servicio Compose `db`, `127.0.0.1:5432` y `http://127.0.0.1:8000/health/ready`, sin iniciar servicios ni contactar producción. E2E se ejecuta únicamente de forma explícita con `-E2E`, que invoca `e2e.ps1` y prepara PostgreSQL en `127.0.0.1:55432`, API en `127.0.0.1:8001` y frontend en `127.0.0.1:5174`. No se combina con `-LocalServices` y Full no ejecuta E2E.

Para instalar el único navegador autorizado:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1 -E2E
```

Para ejecutar la suite E2E:

```powershell
powershell -ExecutionPolicy Bypass -File .\verify.ps1 -E2E
```

La ejecución anterior es headless por defecto. Para ver físicamente Chromium ejecutando exactamente la misma suite:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\verify.ps1 -E2E -Headed
```

`-Headed` sólo es válido junto con `-E2E`; no cambia permanentemente la configuración de Playwright.

Para observar las acciones ralentizadas localmente:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\verify.ps1 -E2E -Headed -SlowMo 700
```

`-SlowMo` acepta valores de `0` a `5000` milisegundos, sólo es válido con `-E2E` y se recomienda para observación/debug local. La validación automática normal debe usar `verify.ps1 -E2E` sin demora.

La ejecución E2E elimina y recrea únicamente el proyecto/volumen Docker `turnelia-e2e`, aplica migraciones sólo sobre esa base y carga un fixture sintético. Si Docker no está disponible, la validación falla; no se simula éxito.

E2E requiere las variables locales `E2E_ADMIN_PASSWORD`, `E2E_JWT_SECRET` y `E2E_DB_PASSWORD`. No se documentan valores, no se crean `.env` automáticamente y las variables no se imprimen.

## Regla para nuevas features

Toda modificación relevante debe incluir tests proporcionales al riesgo. Cambios de permisos deben cubrir casos permitidos y prohibidos; cambios de turnos, disponibilidad, estados, solapamientos y concurrencia cuando corresponda; cambios de pagos, ownership, idempotencia y webhooks.
