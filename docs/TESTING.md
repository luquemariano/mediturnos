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

La colección cubre autenticación, recuperación, roles/ownership, profesionales, pacientes, turnos, disponibilidad, excepciones, feriados, solapamientos, concurrencia, invitaciones de Consultorio, actividad profesional/matrícula condicional, pagos, webhooks, suscripciones, recordatorios, emails, documentos, estudios, evoluciones, perfiles clínicos, notificaciones, storage, rate limiting, health checks, seed y bootstrap. Las reservas de sala se comprueban para invitaciones pendientes y profesionales activos; las invitaciones terminales o vencidas liberan ocurrencias sin borrar su historial. La sesión frontend cubre cierre de sesión y evita que una validación concurrente restaure una cuenta cuyo token ya cambió.

La profundidad de cobertura varía por módulo. Consultar `tests/` para el detalle. Invitaciones: pruebas SQLite de hash/rotación, expiración/revocación, email coincidente, aceptación idempotente, cupo y autorización; PostgreSQL prueba cupo concurrente y exclusión GiST para ocurrencias pendientes. El panel añade pruebas HTTP allowlist y de acceso administrativo, además de pruebas Vitest/RTL de visibilidad condicional, agenda semanal, invitaciones y conflictos sin datos clínicos.

## Frontend

Ubicación: `frontend/tests/`. Usa Vitest, Testing Library, jsdom, TypeScript y Vite. El timeout individual es 15 segundos para absorber variaciones de carga de la suite completa; Testing Library usa un límite asíncrono de 3 segundos para consultas DOM bajo carga.

```powershell
Set-Location frontend
npx vitest run tests
npm run lint
npm run build
```

`npx vitest run tests` es la suite frontend unitaria/de integración canónica para CI. No se usa `npm test` como comando canónico porque su descubrimiento amplio puede incluir `frontend/e2e/` y mezclar Playwright; los E2E se ejecutan únicamente de forma explícita con `verify.ps1 -E2E`.

Hay cobertura de sesión, recuperación, dashboards, agenda, pacientes, profesionales, disponibilidad, prestaciones, suscripciones, estudios, documentos, notificaciones, SEO y panel administrativo de Consultorio. La Entrega 06 comprueba en Vitest/RTL la selección de actividad, campos condicionales, payload de estética sin matrícula/especialidad y validaciones requeridas; Playwright registra prestadores sintéticos de estética y una actividad matriculable. Playwright incluye el acceso condicional al panel, agenda sin información clínica, invitación con proveedor simulado, comprobación móvil sin desbordamiento horizontal, revocación de invitación que libera su ocupación, logout con rechazo de restauración posterior y cambio de cuenta/rol, y rechazo de un profesional no administrador.

La cobertura no es uniforme entre módulos. Consultar `frontend/tests/` para el detalle.

### Comunicaciones staging (Entrega 08A)

Pruebas focalizadas: `python -m pytest tests/test_staging_communications_preflight.py tests/test_staging_communications_integration.py tests/test_staging_safety.py tests/test_whatsapp_appointment_reminder.py tests/test_meta_whatsapp_provider.py tests/test_appointment_reminder_worker_config.py tests/test_appointment_reminders.py tests/test_appointment_reminder_email.py tests/test_appointment_actions_http.py tests/test_whatsapp_webhook.py`. Cubren defaults fake/in-memory, preflight estrictamente staging, presencia de nombres de variables, callback HTTPS, mapping de plantilla, allowlists, rechazo previo al provider, recordatorio e idempotencia, enlaces firmados de confirmación/cancelación, `POST` de acción idempotente y rechazo de config staging en production. Los providers fake/mocks no hacen solicitudes externas.

El preflight manual sólo lee el archivo indicado y no ejecuta Compose ni contacta servicios: `python3 scripts/staging/communications_preflight.py --env-file <archivo-privado-de-staging>`. Su salida enumera nombres y estado, nunca valores. No interpreta el resultado como prueba de entrega de email/WhatsApp, aprobación Meta o disponibilidad del webhook. No hay cambios de esquema en Entrega 08A; el job PostgreSQL existente y E2E se ejecutan como gates de regresión, no porque esta entrega requiera migración.

## Limitaciones actuales

- Playwright está configurado para Chromium y la suite MVP vive en `frontend/e2e/`.
- La ejecución E2E requiere Docker, Chromium instalado y el entorno aislado que prepara `e2e.ps1`.
- SQLite no demuestra compatibilidad PostgreSQL total.
- Tests locales no validan la operación productiva de Render, Aiven, Resend, R2 o Mercado Pago.
- La cobertura PostgreSQL es selectiva.

### PostgreSQL CI

GitHub Actions incluye un job separado llamado `PostgreSQL CI`.
Usa `postgres:17-alpine` como service container efímero, ejecuta Alembic sobre
una base PostgreSQL vacía y después valida secuencialmente los módulos de
concurrencia de turnos, recordatorios, acciones de turnos, ownership clínico,
fundación de Consultorio, módulos recurrentes, invitaciones y catálogo de actividad profesional/matrícula condicional. Los módulos comprueban exclusión
GiST concurrente (incluida la reserva pendiente), cupo concurrente, idempotencia del generador y adyacencia en PostgreSQL. El módulo
de migración comprueba además la cadena
Alembic en una base desechable creada desde cero y carreras concurrentes de
unicidad. El job genera
`postgresql-test-results.xml` y falla si alguno de esos módulos queda
completamente skipped. `tests/test_pagos_postgresql.py` no se incluye en este
job por requerir una variable adicional fuera del contrato actual.

El job es required en Branch Protection tras la validación verde del PR #4.

### Playwright E2E CI — Fases 7A y 7B

El workflow incluye `Playwright E2E CI` como job separado e informativo,
ejecutable con `workflow_dispatch` y, desde Fase 7B, automáticamente en Pull
Requests hacia `main`. Usa PostgreSQL E2E local,
Alembic, seed sintético, Chromium headless y las specs `smoke`, `auth` y
`admin`. En 7A sólo se publican, ante fallo, logs sanitizados de API,
frontend y PostgreSQL; no se publican traces, screenshots ni HTML reports.
Las Fases 7A y 7B quedaron completadas. El PR #5 quedó bloqueado por conflicto de merge y no generó
checks; el PR reconciliado #6 sí generó el run `32600285274` por
`pull_request`, con cuatro jobs verdes y `3 passed (4.7s)` en Playwright. El
job todavía no es required y el Ruleset no fue modificado. Antes de Fase 7C
deben acumularse cinco ejecuciones verdes en al menos tres PRs o actualizaciones,
sin flakiness no explicada, skips inesperados ni inestabilidad de cleanup/readiness.
La primera
validación remota manual sobre `feature/mvp` fue exitosa en el run
`32598856151` (commit `a2124ff`): Chromium instalado, PostgreSQL E2E,
Alembic, seed sintético, API y frontend listos, y `3 passed (4.2s)` en las
tres specs. El cleanup fue exitoso y no se publicaron artifacts al no haber
fallo.

El primer run remoto de Fase 6 (`32597104272`) confirmó Alembic correcto, pero
detectó schema drift causado por el fixture global aplicado sobre PostgreSQL y
un falso negativo del parser JUnit. La corrección condiciona ese fixture para
preservar el esquema migrado y verifica el constraint PostgreSQL antes de
pytest; la fase queda pendiente de revisión final.
La corrección fue validada remotamente en el run `32597419679`: PostgreSQL CI
ejecutó `23 passed, 0 failed, 0 skipped`, verificó el constraint migrado y
confirmó los tres módulos obligatorios mediante JUnit. El PR #4 confirmó los
tres checks required verdes y el merge permitido; el PR fue cerrado sin merge.

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

El E2E del panel Consultorio verifica que un solapamiento recurrente identifique la fecha, franja y profesional ocupante sin datos clínicos, que las duraciones expresadas en horas se conviertan exactamente a minutos al conservar el contrato de la API, que la navegación persista en Inicio/agenda/pacientes/disponibilidad, y que una suspensión con turnos se bloquee mostrando sólo el conteo mientras una ocurrencia libre admita cambios. La suite también verifica que una cuenta profesional no administradora no vea el acceso ni obtenga datos por URL directa.

La ejecución E2E elimina y recrea únicamente el proyecto/volumen Docker `turnelia-e2e`, aplica migraciones sólo sobre esa base y carga un fixture sintético. Si Docker no está disponible, la validación falla; no se simula éxito.

E2E requiere las variables locales `E2E_ADMIN_PASSWORD`, `E2E_JWT_SECRET` y `E2E_DB_PASSWORD`. No se documentan valores, no se crean `.env` automáticamente y las variables no se imprimen.

## Regla para nuevas features

Toda modificación relevante debe incluir tests proporcionales al riesgo. Cambios de permisos deben cubrir casos permitidos y prohibidos; cambios de turnos, disponibilidad, estados, solapamientos y concurrencia cuando corresponda; cambios de pagos, ownership, idempotencia y webhooks.

## Staging (Entrega 07)

La configuración se valida sin imprimir secretos:

```bash
python3 scripts/staging/generate_env.py /ruta/privada/.env.staging
STAGING_ENV_FILE=/ruta/privada/.env.staging scripts/staging/manage.sh validate
STAGING_ENV_FILE=/ruta/privada/.env.staging scripts/staging/manage.sh up
STAGING_ENV_FILE=/ruta/privada/.env.staging scripts/staging/manage.sh health
```

`update` construye imágenes etiquetadas con el SHA corto del checkout; para volver a una versión validada preservada localmente, establecer `STAGING_IMAGE_TAG=<tag-anterior>` y usar `scripts/staging/manage.sh rollback`. El rollback verifica que existan ambas imágenes y no construye nada. Sólo es seguro si el esquema de base conserva compatibilidad con la versión anterior; restaurar un dump es una operación aislada separada y nunca sobre producción.

En Windows, usar Git Bash con `STAGING_ENV_FILE` apuntando al archivo externo. Ejecutar migraciones sólo sobre la base disposable staging y habilitar la semilla sintética sólo explícitamente (`STAGING_SEED_ENABLED=true`). Backup/restore: `scripts/staging/backup_restore_check.sh backup` y luego `restore-check`. La restauración crea y elimina una base temporal dentro del mismo PostgreSQL staging. Limpieza requiere `STAGING_REMOVE_CONFIRM=turnelia-staging`; verifica antes que los recursos Docker estén etiquetados como staging y tengan servicios, volúmenes y redes permitidos. Los procedimientos nunca leen una copia productiva.

Validación local de la Entrega 07 en Docker Desktop: PostgreSQL 18 saludable; `alembic upgrade head` en vacío hasta `a7b8c9d0e1f2`; seed sintético idempotente dos veces; backup/checksum/restore correctos; API y frontend saludables; puertos sólo loopback; `robots.txt` bloqueado y `X-Robots-Tag: noindex, nofollow, noarchive`. Esta prueba local no acredita disponibilidad ni configuración del VPS.

Las cuentas profesionales seed usan direcciones `staging-*@turnelia.com.ar` válidas para `/auth/login`; `python -m app.scripts.seed_staging --actualizar-emails-sinteticos` renombra de forma idempotente los alias legacy `@example.invalid`, conservando hashes de contraseña y registros clínicos. El seed QA del Consultorio crea cuatro integrantes activos, pacientes propios, un paciente compartido entre las dos profesionales clínicas con registros separados, módulos recurrentes materializados hasta 90 días y turnos futuros. No crea cuentas de login para pacientes. `tests/test_staging_seed_postgresql.py` crea una base PostgreSQL efímera, aplica Alembic y ejecuta el seed dos veces sobre la misma base; verifica cuatro vínculos activos únicos, diez turnos y cero invitaciones pendientes. Las pruebas PostgreSQL cubren el conteo privado de turnos al bloquear una suspensión y la modificación de un módulo libre; E2E verifica ambas rutas en una base Docker exclusiva `turnelia-e2e`.

Pendiente de preproducción remota: acceso SSH autorizado para inspección, DNS `staging.turnelia.com.ar`, validación de espacio/puertos/containers/backups/cron y revisión de Caddy antes de configurar proxy/TLS. No desplegar ni recargar Caddy como parte de la Entrega 07.

Para correo real de prueba (aún apagado): `STAGING_EMAIL_SEND_ENABLED=true`, `EMAIL_PROVIDER=resend`, `RESEND_API_KEY`, `EMAIL_FROM` verificado y `STAGING_EMAIL_ALLOWLIST` con la única dirección previamente autorizada. El owner debe entregar esa dirección y credenciales Resend de staging; no hubo envíos reales.

WhatsApp fake se valida mediante las suites backend existentes de recordatorios, proveedor, configuración y webhook. Meta staging queda apagada; al habilitarla requiere `STAGING_WHATSAPP_META_ENABLED=true`, `STAGING_WHATSAPP_META_TEST_NUMBER_CONFIRMED=true`, `STAGING_WHATSAPP_PROVIDER=meta`, IDs Meta de test incluidos literalmente en las allowlists `STAGING_WHATSAPP_PHONE_NUMBER_ID_ALLOWLIST` y `STAGING_WHATSAPP_BUSINESS_ACCOUNT_ID_ALLOWLIST`, credenciales dedicadas y `PUBLIC_API_URL=https://api.staging.turnelia.com.ar`. Callback: `https://api.staging.turnelia.com.ar/webhooks/whatsapp`. No se verificó la existencia de Meta App/número de prueba y no se envió WhatsApp.
