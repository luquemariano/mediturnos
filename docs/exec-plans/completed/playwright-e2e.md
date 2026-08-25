# Exec Plan: Playwright y E2E

Estado: COMPLETADO

## Objetivo

Diseñar e incorporar una primera capa reproducible de pruebas end-to-end con Playwright para Turnelia, diferenciada de pytest, Vitest y las pruebas de integración existentes. Esta fase crea el contrato de implementación; no instala Playwright ni modifica todavía el código de la aplicación o los tests.

## Contexto y evidencia actual

- El frontend es React/Vite y enruta mediante `window.location.pathname`, sin React Router.
- El login llama a la API, guarda el JWT en `localStorage` bajo `access_token` y navega a `/app`.
- Existen vistas protegidas de dashboard, agenda, turnos y administración.
- La API expone health checks en `/health/live` y `/health/ready`.
- Actualmente no hay dependencia, configuración ni suite Playwright.
- `setup.ps1` y `verify.ps1` no instalan ni ejecutan E2E en su contrato actual.

## Alcance

1. Instalar Playwright como dependencia de desarrollo del frontend y fijar la versión en el lockfile.
2. Crear una configuración explícita para Chromium, headless por defecto y ejecución visible sólo cuando se solicite.
3. Crear la primera suite en `frontend/e2e/` junto con utilidades mínimas, sin duplicar pruebas unitarias o de integración.
4. Integrar la ejecución como capacidad opt-in del Harness, conservando Quick y Full sin E2E por defecto.
5. Documentar precondiciones, datos, artefactos, seguridad y diagnóstico de fallos.

## Fuera de alcance

- No probar producción, Render, Aiven, R2, Resend, Mercado Pago ni URLs externas.
- No probar pagos reales, emails reales, cargas reales a R2 ni webhooks externos.
- No incorporar CI, Playwright Cloud, múltiples navegadores, dispositivos móviles ni visual regression.
- No sustituir pytest, Vitest, lint, build ni las pruebas PostgreSQL selectivas.
- No modificar migraciones, seed, lógica funcional ni tests oficiales existentes como parte de este plan.

## Arquitectura E2E

El diseño cerrado usa una infraestructura E2E separada: PostgreSQL en `127.0.0.1:55432`, API en `http://127.0.0.1:8001` y frontend en `http://127.0.0.1:5174`. La inspección del repositorio no encontró conflictos documentados con esos puertos. Nunca se usarán dominios productivos ni los puertos normales como sustituto silencioso.

La configuración será `frontend/playwright.config.ts`, con `testDir: frontend/e2e`, `baseURL` `http://127.0.0.1:5174`, Chromium, timeouts explícitos y aislamiento por test.

## Entorno local

El entorno objetivo es una máquina con Node/npm, dependencias del frontend, Python y Docker. PostgreSQL, API y frontend E2E serán iniciados por `e2e.ps1` mediante configuración/procesos dedicados. No se utilizarán Aiven, Render ni la instancia productiva.

La instalación del navegador debe ser explícita (`npx playwright install chromium`) y no una consecuencia silenciosa de Quick. Deben documentarse las precondiciones y el puerto ocupado antes de ejecutar E2E.

## Base de datos y datos

La suite utilizará PostgreSQL local en Docker dedicado exclusivamente a E2E: proyecto Compose con nombre explícito, base y usuario sintéticos, volumen exclusivo y host `127.0.0.1:55432`. No reutilizará el volumen o database de desarrollo, Aiven ni ninguna base productiva. El reset podrá destruir ese proyecto/volumen porque contendrá exclusivamente datos sintéticos.

Antes de cada ejecución completa, `e2e.ps1` eliminará únicamente el entorno E2E, creará PostgreSQL limpio, esperará readiness, aplicará migraciones, cargará el fixture, ejecutará Playwright y limpiará exclusivamente los recursos creados. Las migraciones pueden ejecutarse automáticamente porque la base fue creada exclusivamente para testing; esto no modifica la política normal de `setup.ps1` ni `verify.ps1`. Debe existir una protección fuerte basada en entorno E2E, host local, identificación de database y puerto esperado; ante cualquier discrepancia el reset fallará.

## Usuarios de prueba

Los usuarios demo configurables son administrador y profesional mediante `DEMO_ADMIN_EMAIL`, `DEMO_ADMIN_PASSWORD`, `DEMO_PROFESSIONAL_EMAIL` y `DEMO_PROFESSIONAL_PASSWORD`; los valores no se incluirán en el repositorio ni en el plan. El profesional puede ser redirigido a onboarding si su estado no está completo.

La primera implementación creará una cuenta `administrador` sintética exclusiva de E2E. Sus credenciales serán variables locales E2E, fuera de Git y nunca productivas; no se imprimirán passwords. El fixture será versionable, mínimo, determinista, idempotente sobre una DB recién creada, sintético, sin IDs productivos, sin servicios externos y rechazará cualquier entorno que no cumpla las señales E2E.

## Primera suite propuesta

1. Smoke: el frontend E2E carga, se ve la pantalla esperada y la API E2E está ready.
2. Autenticación de administrador: abrir login, ingresar credenciales E2E, llegar a `/app`, verificar un elemento semántico estable, cerrar sesión y volver al estado no autenticado.
3. Autorización/navegación protegida: el administrador autenticado abre la vista administrativa `cuentas`, implementada por `CuentasAdmin` y accesible desde el dashboard. Es la pantalla elegida porque existe hoy, no requiere agenda profesional ni pagos y sus datos provendrán del fixture; el test será read-only.

El primer incremento debe ser pequeño y estable. No incluirá recuperación de contraseña, pagos, notificaciones ni carga de estudios hasta contar con dobles locales y datos reproducibles.

## Selectores

Priorizar roles y nombres accesibles (`getByRole`, `getByLabel`, `getByText` sólo cuando sea estable). Si un control carece de un nombre accesible estable, añadir en la implementación futura un `data-testid` semántico y mínimo. No seleccionar por clases CSS, posición DOM, texto incidental ni estilos.

## Seguridad

- Ejecutar únicamente contra `127.0.0.1`/`localhost`.
- Leer credenciales desde variables de entorno o fixtures locales fuera de Git.
- Nunca imprimir contraseñas, JWT, cookies, tokens, `DATABASE_URL` ni contenido clínico.
- No guardar `storageState` con sesión en una ruta versionada.
- Revisar screenshots, videos y traces antes de compartirlos: pueden contener PII o datos de sesión.

## Instalación y configuración Playwright

La configuración actual usa Chromium, `headless: true`, workers `1`, retries local `0`, `baseURL: http://127.0.0.1:5174`, timeout de test 30 s, expect 5 s, navegación 15 s, screenshot sólo en fallo, trace `retain-on-failure`, video desactivado, reporter line/list más HTML local sin apertura automática. `verify.ps1 -E2E` ejecuta la suite headless; `verify.ps1 -E2E -Headed` pasa la opción oficial `--headed` sólo para esa ejecución. Ambos comandos ejecutan exactamente la misma suite.

## Estructura propuesta

```text
frontend/
  playwright.config.ts
  e2e/
    fixtures/
    auth.spec.ts
    smoke.spec.ts
```

Los nombres son una propuesta; no deben crearse hasta aprobar este plan y cerrar la estrategia de datos.

## Artefactos

Screenshots sólo ante fallo, traces para el primer retry/fallo según configuración y videos desactivados. La futura implementación agregará a `.gitignore` `frontend/test-results/`, `frontend/playwright-report/` y `frontend/.auth/` según las rutas reales; si todo queda dentro de `test-results`, no duplicará reglas. Nunca se versionarán storage state, cookies, JWT, traces, screenshots, videos ni reports.

## Configuración de procesos y readiness

El frontend E2E recibirá explícitamente `VITE_API_URL=http://127.0.0.1:8001`, que es la variable comprobada en `frontend/src/api/api.ts` y `frontend/.env.example`; no heredará URLs productivas ni modificará `.env`. La API E2E recibirá entorno E2E, `DATABASE_URL` de la base E2E y configuración local/sintética. Resend, Mercado Pago y R2 reales no se usarán; si login/smoke exigiera alguno sin alternativa local ya soportada, sería un bloqueo explícito.

PostgreSQL deberá estar healthy antes de migrar. La API se comprobará mediante `http://127.0.0.1:8001/health/ready` y el frontend mediante una respuesta HTTP exitosa de `http://127.0.0.1:5174`. `e2e.ps1` hará polling con timeout limitado e intervalo corto; no usará sleeps arbitrarios.

## Integración con `setup.ps1`

El setup normal continuará sin instalar browsers. La futura interfaz `setup.ps1 -E2E` preparará el setup normal, instalará dependencias npm por el flujo existente y ejecutará sólo `npx playwright install chromium`; no ejecutará E2E, no creará `.env` ni seedeará datos.

## Integración con `verify.ps1`

La interfaz es mutuamente excluyente: sin argumentos/`-Quick` = Quick, `-Full` = Full y `-E2E` = E2E. `-Headed` sólo es válido junto con `-E2E`; `-Quick -Headed`, `-Full -Headed` y `-Headed` devuelven `2`. `-LocalServices` conserva su semántica actual para Quick/Full y no es requisito de E2E. Full no ejecuta E2E. `verify.ps1 -E2E` valida precondiciones, invoca `e2e.ps1` y propaga su exit code; Chromium ausente, Docker no disponible o fallo de suite devuelven `1`, uso inválido devuelve `2`.

`e2e.ps1` orquestará exclusivamente E2E, con `try/finally`, handles/PIDs de los procesos hijos y cleanup sólo de lo que creó. Si un puerto E2E está ocupado, fallará claramente sin reutilizar un servidor desconocido. No matará procesos Python/Node globalmente.

## Manejo de fallos y flakiness

Un fallo debe indicar spec, test, URL/endpoint local implicado y ruta del artefacto sanitizado, sin contenido sensible. Workers `1`, retries locales `0`, waits semánticos, polling de readiness, reset completo previo y ausencia de internet son obligatorios para el MVP. Un test se considerará flaky sólo con evidencia reproducible; no se aprobará ocultándolo con retries.

## Riesgos

- La ausencia de una base/fixture aislada puede contaminar ejecuciones y hacer no reproducible la suite.
- El onboarding del profesional puede cambiar el destino posterior al login.
- Los selectores basados en la UI actual pueden requerir pequeños atributos accesibles.
- Chromium y sus artefactos incrementan tiempo y espacio local.
- Los tres fallos Vitest preexistentes documentados en el Harness son independientes de Playwright.

## Decisiones abiertas restantes

No quedan decisiones funcionales abiertas que bloqueen la implementación. Quedan únicamente detalles mecánicos menores: nombres finales de archivos internos del fixture, implementación concreta del Compose E2E y el formato exacto de los mensajes de diagnóstico, siempre sujetos a las políticas cerradas en este plan.

La ruta administrativa MVP queda fijada como la vista `cuentas`/`CuentasAdmin`; no se incorporan todavía agenda profesional ni pagos.

## Pasos de implementación

1. Cerrar las decisiones de datos, usuario y orquestación.
2. Añadir la dependencia/configuración de Playwright y verificar Chromium localmente.
3. Crear fixtures aislados y helpers de login sin exponer secretos.
4. Implementar smoke, login/logout y autorización.
5. Añadir selectores accesibles mínimos sólo donde la UI lo requiera.
6. Incorporar artefactos locales y reglas de limpieza/ignore.
7. Integrar el comando opt-in de verify y documentar precondiciones.
8. Ejecutar la validación E2E en una fase posterior, separada de esta creación del plan.

## Validación futura

- Instalación limpia desde `frontend/package-lock.json`.
- API y frontend locales accesibles y health check correcto.
- Base E2E aislada, inicializada y reiniciable.
- Smoke, autenticación y autorización reproducibles en Chromium.
- Fallos con artefactos sanitizados y exit codes documentados.
- Quick y Full conservan su contrato cuando E2E no se solicita.

La implementación instaló Playwright y Chromium, creó la infraestructura y ejecutó las validaciones estáticas. Durante el debugging se corrigió el arranque de Vite: `Start-Process` no puede ejecutar directamente el wrapper PowerShell `npm`; se usa `npm.cmd` con stdout/stderr capturados. También se reforzó readiness PostgreSQL con una consulta real `SELECT 1`, se preserva el primer fallo antes del cleanup y se limpia el árbol de procesos creado por Vite.

La ejecución headed autorizada completó PostgreSQL, migraciones, fixture, API ready, frontend ready, Chromium visible y los tres tests: `3 passed (9.4s)`. El cleanup E2E terminó correctamente. Los fallos previos fueron diagnósticos y no defectos funcionales de Turnelia: wrapper `npm` incompatible con `Start-Process`, readiness de PostgreSQL demasiado optimista, selector que buscaba `email` mientras la UI expone `Correo electrónico` y dominio sintético reservado rechazado por `EmailStr`.

La ejecución E2E requiere, sólo en el entorno local de la sesión, `E2E_ADMIN_PASSWORD`, `E2E_JWT_SECRET` y `E2E_DB_PASSWORD`; el JWT debe tener al menos 32 caracteres. No se generan archivos `.env`, no se imprimen valores y no se incluyen secretos en fixtures, tests ni configuración. Compose resuelve `E2E_DB_PASSWORD` desde el entorno del proceso y `DATABASE_URL` se construye únicamente en memoria para Alembic, fixture y API. La fase Compose se marca antes de `down/up`; el cleanup valida mecánicamente el project name `turnelia-e2e` y la ruta exacta `docker-compose.e2e.yml`, por lo que también intenta `down -v` si `up` falla parcialmente y nunca afecta el Compose normal.

La password PostgreSQL E2E ya no está versionada: `docker-compose.e2e.yml` usa la interpolación obligatoria `E2E_DB_PASSWORD`, y el orquestador construye la URL de conexión en memoria con la password codificada para URL. Las tres variables se validan antes de cualquier operación Compose. La prueba sin `E2E_DB_PASSWORD` devolvió exit `1` sin crear recursos; con valores sintéticos sólo en sesión, la ejecución headed terminó con `3 passed` y cleanup correcto. La salida no mostró password, JWT ni `DATABASE_URL`.

## Criterio de finalización del plan

La Fase 3 fue aprobada para cierre. El plan conserva el objetivo, alcance, arquitectura, fixture sintético, contratos de `e2e.ps1`, `setup.ps1 -E2E`, `verify.ps1 -E2E`, modo `-Headed`, suite de 3 tests, secrets por variables locales, cleanup seguro, ejecución real con exit `0` y `3 passed`, y riesgos residuales no bloqueantes.

La mejora posterior de observación local admite `verify.ps1 -E2E -Headed -SlowMo 700`. SlowMo se pasa sólo durante la ejecución mediante `PLAYWRIGHT_SLOW_MO`, con default `0` y sin modificar permanentemente la configuración.
