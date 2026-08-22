# Exec Plan — setup y verificación local del Harness

Estado: **COMPLETADO**

Este plan define el contrato de `setup.ps1` y `verify.ps1`. Los scripts fueron implementados y la revisión final los aprobó como **IMPLEMENTACIÓN APROBADA CON RIESGOS RESIDUALES**.

## Progreso de implementación

Los scripts fueron creados en la raíz durante la Fase 2. Quick terminó correctamente con warnings esperados. Full ejecutó pytest backend, tests frontend, lint y build: pytest, lint y build pasaron; Vitest falló en tres casos preexistentes de `frontend/tests/excepcionesDisponibilidad.test.tsx`. No se modificaron esos tests. `-LocalServices` se ejecutó en modo read-only y falló porque Docker daemon no estaba disponible; no inició servicios. No se ejecutó setup, seed ni migraciones.

## Objetivo

Diseñar dos scripts PowerShell reproducibles para preparar un entorno local y obtener feedback claro sobre el repositorio, sin tocar secretos, destruir datos ni depender de servicios productivos.

## Contexto

Turnelia tiene backend Python/FastAPI, frontend React/TypeScript/Vite, tests pytest/Vitest, Docker Compose con PostgreSQL local, Alembic, `.env.example`, Render declarado y PostgreSQL productivo documentado en Aiven. Las fuentes de comandos y dependencias son `AGENTS.md`, `README.md`, `requirements.txt`, `frontend/package.json`, `docker-compose.yml` y `render.yaml`.

## Alcance

- `setup.ps1`: preparar dependencias locales de backend y frontend de forma idempotente.
- `verify.ps1`: ejecutar validaciones Quick/Full y, sólo con opt-in, comprobaciones de servicios locales.
- Ambos deben ejecutarse desde la raíz del repositorio, validar que la raíz es válida, usar paths relativos, emitir mensajes concisos, propagar fallos externos y restaurar el directorio de trabajo tras entrar temporalmente en `frontend/`.

## Fuera de alcance

- Crear los scripts en esta fase.
- Instalar Playwright o crear E2E.
- Modificar código, tests o migraciones.
- Ejecutar seed automáticamente.
- Conectarse a Aiven, Render, Resend, Mercado Pago o R2.
- Hacer commit, push, checkout, merge o Git destructivo.

## Arquitectura afectada

Los scripts serán PowerShell sobre Windows y coordinarán herramientas ya existentes: `.venv`, `requirements.txt`, `frontend/package-lock.json`, `frontend/package.json`, Docker Compose, pytest, Vitest, oxlint, Vite, Alembic y health checks locales. No agregarán una capa de aplicación ni dependencias nuevas.

## Seguridad

- No imprimir `.env`, `DATABASE_URL`, JWT, contraseñas, API keys, secretos de webhooks, `APPOINTMENT_ACTION_SECRET` ni `STUDY_ACCESS_SECRET`.
- No modificar `.env`, completar secretos ni copiar credenciales productivas. Si falta, informar que el usuario debe consultar `.env.example` y la documentación.
- No depender de credenciales productivas.
- No ejecutar seed ni migraciones automáticamente.
- No eliminar `.venv`, volúmenes Docker ni datos locales.
- No hacer operaciones Git destructivas ni commit/push.

## Decisiones cerradas de prerrequisitos

El repositorio no fija versiones mínimas de PowerShell, Python, Node, npm o Docker mediante metadata, lockfiles, documentación, Dockerfile o configuración. Por ello, los scripts comprobarán presencia y obtendrán la versión, pero no bloquearán por una versión mínima no documentada. Una herramienta ausente será error sólo cuando sea necesaria para el paso solicitado.

## Diseño de `setup.ps1`

### Contrato de ejecución

Debe ejecutarse desde la raíz. Antes de operar debe comprobar archivos/directorios identificadores del repositorio, como `AGENTS.md`, `requirements.txt` y `frontend/package.json`. No usará `C:\Proyectos\mediturnos` ni otros paths absolutos. Debe conservar el directorio original si entra en `frontend/`.

### Python y `.venv`

- Si `.venv` no existe, crearla con el Python disponible.
- Si `.venv` existe y `.venv\Scripts\python.exe` funciona, reutilizarla.
- Si existe pero su Python no es ejecutable o está claramente inutilizable, no eliminarla ni recrearla: finalizar con error y mostrar remediación segura.
- Todas las operaciones backend usarán `.\.venv\Scripts\python.exe` después de crear/verificar el entorno.

### Dependencias backend

Ejecutar `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`. `pip` determinará qué dependencias ya están satisfechas; no se implementará comparación propia ni se actualizará fuera de `requirements.txt`.

### Dependencias frontend

Si existe `frontend/package-lock.json`, ejecutar `npm ci` dentro de `frontend/`. Es deliberadamente reproducible y puede eliminar/recrear `node_modules`; ese efecto local es aceptable en setup. No modifica código fuente ni configuración. Un lockfile inconsistente debe producir error; no habrá fallback silencioso a `npm install`.

### `.env`

Existe `.env.example`. El comportamiento por defecto nunca sobrescribe `.env`, completa secretos ni copia credenciales productivas. Si falta `.env`, informar qué ejemplo y documentación consultar; `verify.ps1 -Quick` no lo considera fallo automáticamente: continúa si el check no lo necesita y clasifica como precondición faltante sólo el check que requiera `.env`. No se crea ni modifica `.env`.

### Docker, seed y migraciones

Comprobar Docker como herramienta disponible, pero no iniciar Docker ni `docker compose up` por defecto. Servicios locales requieren opt-in explícito. `setup.ps1` no ejecutará seed ni migraciones automáticamente.

## Diseño de `verify.ps1`

### Interfaz cerrada

- Sin argumentos: equivale a `-Quick`.
- `-Quick` y `-Full` son mutuamente excluyentes.
- `-LocalServices` es un opt-in independiente para checks Docker/PostgreSQL/health locales.
- No se conectará a servicios productivos.

### Quick

Checks obligatorios: raíz válida, Git disponible, Python utilizable, Node/npm disponibles, `.venv` cuando sea necesaria, import básico del backend, existencia/consistencia básica de archivos frontend relevantes y revisión Git no destructiva.

Warnings: working tree modificado, archivos untracked, Docker ausente si no se pidió `-LocalServices` y Playwright no incorporado.

Quick no ejecuta pytest completo, Vitest completo, lint, build, Docker Compose, PostgreSQL, health checks, migraciones, seed ni servicios externos.

### Full

Incluye Quick y además:

- pytest backend;
- tests Vitest frontend;
- lint frontend;
- build frontend.

Un fallo en cualquiera de esas verificaciones obligatorias devuelve error. Full no conecta por defecto con Aiven, Render, Resend, Mercado Pago, R2 ni otros servicios externos. Playwright/E2E permanece **NO INCORPORADO** y no bloquea.

### LocalServices

Con `-LocalServices` solicitado:

- Docker CLI ausente: error.
- Docker CLI presente pero daemon apagado: error.
- PostgreSQL local inaccesible: error.
- Health endpoint local sin servicio activo: error.

Sin `-LocalServices`, estos checks se omiten sin warning obligatorio. Nunca se conectará a producción.

### Migraciones

`verify.ps1` no ejecutará migraciones. Puede comprobar presencia/configuración de Alembic y consistencia no destructiva. Toda verificación futura contra una DB real requerirá opt-in y diseño específico.

## Códigos de salida

- `0`: todas las verificaciones obligatorias del modo pasaron; puede haber warnings.
- `1`: falló una o más verificaciones obligatorias.
- `2`: error de uso o precondición que impide ejecutar correctamente el script.

Warnings no producen código distinto de cero por sí solos. Los scripts deben preservar e interpretar `$LASTEXITCODE` de comandos externos y convertir sus fallos en el resultado correspondiente.

## Secretos y archivos sensibles

`verify.ps1` sólo hará comprobaciones defensivas simples: estado Git de `.env` y nombres de archivos sensibles que no deberían versionarse. La política es:

- `.env` trackeado por Git: **FAIL**, exit code `1`, porque no debe versionarse.
- Secreto o valor sensible detectado en archivo versionado por las comprobaciones simples definidas: **FAIL**, exit code `1`.
- `.env` local no trackeado: **WARN**, exit code `0` si no hay otro fallo obligatorio.
- Archivo potencialmente sensible local no trackeado: **WARN**, exit code `0` si no hay otro fallo obligatorio.
- `.env` ausente: no es fallo automático de Quick; sólo es precondición faltante del check que lo requiera.

En fallos o warnings se mostrará únicamente archivo, categoría/tipo y ubicación sanitizada cuando corresponda. Nunca se mostrará valor, token, password, connection string ni contenido sensible.

Un scanner heurístico profundo de contenidos queda **FUERA DE ALCANCE / FUTURA MEJORA**.

## Tabla de checks

| Check | Quick | Full | LocalServices | Resultado |
|---|---:|---:|---:|---|
| Raíz válida | Sí | Sí | No | Fallo si no corresponde al repo |
| Git disponible/revisión no destructiva | Sí | Sí | No | Fallo de herramienta; cambios/untracked warning |
| Python y `.venv` | Sí | Sí | No | Fallo si son necesarios y no utilizables |
| Node/npm y archivos frontend | Sí | Sí | No | Fallo si faltan para el modo |
| Import básico backend | Sí | Sí | No | Fallo |
| pytest backend | No | Sí | No | Fallo |
| Vitest frontend | No | Sí | No | Fallo |
| Lint frontend | No | Sí | No | Fallo |
| Build frontend | No | Sí | No | Fallo |
| Docker CLI/daemon | No | No | Sí | Fallo sólo con opt-in |
| PostgreSQL local | No | No | Sí | Fallo sólo con opt-in |
| Health local | No | No | Sí | Fallo sólo con opt-in |
| Alembic sin aplicar cambios | No | Sí | No | Fallo si la comprobación no destructiva falla |
| `.env` trackeado por Git | Sí | Sí | No | FAIL, exit code `1`; nunca imprime contenido |
| Secreto/valor sensible en archivo versionado (check simple) | Sí | Sí | No | FAIL, exit code `1`; sólo categoría y ubicación sanitizada |
| `.env` local no trackeado | Sí | Sí | No | WARN; exit code `0` si no hay otro fallo obligatorio |
| Archivo potencialmente sensible local no trackeado | Sí | Sí | No | WARN; exit code `0` si no hay otro fallo obligatorio |
| `.env` ausente | Sí | Sí | No | Continúa si no es necesario; precondición faltante sólo para el check que lo requiera |
| Playwright/E2E | No | No | No | Skip; NO INCORPORADO |
| Servicios externos | No | No | No | Skip; no son requisito local |

## Idempotencia

Ejecutar setup varias veces es válido: un `.venv` válido se reutiliza, `pip install -r requirements.txt` puede repetirse, `npm ci` puede recrear `node_modules`, `.env` nunca se sobrescribe, los volúmenes Docker nunca se eliminan y los datos locales nunca se destruyen. Verify debe ser esencialmente de lectura salvo efectos locales documentados de las herramientas.

## Mensajes y manejo de errores

Usar mensajes breves con prefijos `[OK]`, `[WARN]`, `[FAIL]` y `[SKIP]`. No imprimir trazas enormes salvo que el fallo externo necesite diagnóstico. Cada fallo debe indicar causa y remediación segura; no continuar silenciosamente con una precondición incumplida.

## Dependencias

No se agregan dependencias nuevas. Backend: `requirements.txt`. Frontend: `frontend/package-lock.json` y `frontend/package.json`. Herramientas externas: PowerShell, Python, Node/npm y Docker.

## Riesgos

- Versiones locales no fijadas explícitamente.
- `.env` ausente o incompatible.
- SQLite de tests no representa toda la compatibilidad PostgreSQL.
- Docker ausente o daemon apagado.
- `npm ci` recrea `node_modules` localmente.
- Detección simple de secretos tiene alcance limitado.
- Los checks locales podrían modificar caches, pero no deben destruir datos ni configuración.

## Decisiones abiertas restantes

No quedan decisiones funcionales abiertas que bloqueen la implementación. La futura implementación sólo deberá resolver detalles puramente mecánicos coherentes con este plan, como ubicación de helpers y formato exacto de mensajes; no podrá cambiar la política de `.env`, archivos sensibles o exit codes.

## Pasos de implementación futura

1. Implementar validación de raíz y contrato de ejecución.
2. Implementar `setup.ps1` con `.venv`, pip, `npm ci` y tratamiento seguro de `.env`.
3. Implementar `verify.ps1` con Quick por defecto, Full y `-LocalServices`.
4. Propagar códigos de salida y `$LASTEXITCODE`.
5. Revisar no exposición de secretos y no destrucción de datos.
6. Validar escenarios con/sin `.venv`, `.env`, Docker y dependencias instaladas.
7. Ejecutar revisión Builder → Reviewer.

## Validación

La futura implementación deberá validarse en máquinas con `.venv` existente y ausente, `.env` existente y ausente, lockfile consistente/inconsistente, Docker disponible/no disponible y cambios Git preexistentes. No deberá consultar producción.

## Documentación a actualizar

Después de implementar y revisar, actualizar `AGENTS.md`, `docs/TESTING.md`, `docs/DEPLOYMENT.md`, `docs/ROADMAP.md` y, si corresponde, `README.md`. `docs/CURRENT_STATE.md` sólo debe declarar scripts implementados cuando realmente existan.

## Riesgos residuales de la implementación actual

- La salida de algunos comandos externos puede ser extensa cuando fallan.
- La detección de archivos sensibles es deliberadamente simple y sólo cubre nombres/estado Git definidos por el contrato.
- Full detecta tres fallos preexistentes de Vitest en `frontend/tests/excepcionesDisponibilidad.test.tsx`; no son defectos del Harness ni bloquean su cierre.
- `-LocalServices` comprueba exclusivamente Docker local, `db` de Compose, `127.0.0.1:5432` y `127.0.0.1:8000/health/ready`; si Docker daemon no está disponible, omite checks dependientes y devuelve fallo acumulado.
- La detección de secretos es deliberadamente limitada y no implementa escaneo heurístico profundo.
- `-LocalServices` no inicia servicios por diseño.
- La salida de herramientas externas puede ser extensa ante fallos.

## Criterio de finalización

El plan queda completado porque ambos scripts están implementados, son idempotentes y seguros conforme al contrato, tienen validación documentada, no dependen de producción y la documentación canónica refleja su comportamiento real. La aprobación final conserva los riesgos residuales indicados arriba.
