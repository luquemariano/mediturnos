# Decisiones registradas

Registro ligero de decisiones demostrables y revisables.

## DEC-001 — PostgreSQL como base productiva

Tipo: convención vigente del sistema. No se conoce el razonamiento histórico original.

`docker-compose.yml`, `render.yaml` y `app/database/connection.py` muestran PostgreSQL para producción/deployment y SQLite principalmente para tests. Los cambios deben preservar PostgreSQL.

## DEC-002 — Alembic para cambios persistentes

Tipo: restricción arquitectónica actual.

El esquema evoluciona mediante `alembic/versions/`; `app.scripts.start` aplica `alembic upgrade head` antes de iniciar la API.

## DEC-003 — React, TypeScript y Vite

Tipo: stack actual derivado de implementación.

`frontend/package.json` y `frontend/src/` establecen el stack. El routing manual actual no debe describirse como React Router.

## DEC-004 — JWT para sesión

Tipo: mecanismo actual derivado de implementación.

La API usa Bearer JWT y el frontend conserva `access_token` en `localStorage`, con controles de rol y ownership.

## DEC-005 — Render como deployment declarado

Tipo: deployment declarado en configuración; operación real NO DETERMINADA.

`render.yaml` declara API Docker, Static Site y Cron, con health check `/health/ready`.

## DEC-006 — Abstracción de email

Tipo: convención vigente derivada de implementación; entrega real NO DETERMINADA.

El código soporta proveedor `in_memory` para entornos controlados y Resend para el deployment declarado. Entrega real NO DETERMINADA.

## DEC-007 — Storage configurable

Tipo: capacidad actual derivada de implementación; uso productivo NO DETERMINADO.

Existe una abstracción con R2 y fake en `app/integrations/storage/`; el uso productivo de R2 es NO DETERMINADO.

## DEC-008 — Recordatorios mediante worker/cron

Tipo: comportamiento implementado y deployment declarado; ejecución real NO DETERMINADA.

`app.scripts.process_appointment_reminders` está declarado en Render cada 15 minutos; su ejecución real NO DETERMINADA.

## DEC-009 — Pagos clínicos y suscripciones SaaS separados

Tipo: restricción arquitectónica actual derivada de implementación.

Servicios, variables, modelos, endpoints y tests distinguen ambos flujos Mercado Pago.

## DEC-010 — Preservación de naming histórico

Tipo: convención vigente de compatibilidad.

Turnelia es la marca; `mediturnos`/`MediTurnos` se conserva donde es identificador técnico o histórico. Cualquier renombrado requiere tarea controlada.

## DEC-011 — Protección de la rama `main`

Tipo: control de repositorio verificado en GitHub; Fase 5 cerrada.

El repositorio utiliza el Ruleset activo `Turnelia main protection`, dirigido
únicamente a `refs/heads/main`. Exige Pull Request y los checks `Backend CI` y
`Frontend CI`, con cero aprobaciones obligatorias y sin exigir actualización
estricta de la rama. Bloquea force-push y eliminación de `main`. El bypass
administrativo está limitado a Pull Requests. No incluye PostgreSQL CI,
Playwright CI ni gates de deployment. El fallback Classic queda documentado
en el Exec Plan. La validación roja del PR #2 confirmó el bloqueo y la
validación verde del PR #3, run
`32595185386`, terminó `CLEAN`/`MERGEABLE` sin bypass; el PR fue cerrado sin
merge. Estado final: Fase 5 cerrada.

## DEC-012 — PostgreSQL CI requerido

Tipo: decisión de Harness implementada y validada remotamente.

PostgreSQL CI se ejecuta como job separado con `postgres:17-alpine`, variables
sintéticas, Alembic y tres módulos PostgreSQL seleccionados. Se ejecuta
secuencialmente y verifica mediante JUnit que ningún módulo obligatorio quede
completamente skipped. El Ruleset `Turnelia main protection` lo exige junto a
`Backend CI` y `Frontend CI`. El PR #4, run `32597812092`, confirmó los tres
checks verdes y merge permitido sin bypass; el PR fue cerrado sin merge.

## DEC-013 — Playwright E2E CI informativo

Tipo: decisión de Harness implementada, validada remotamente y aprobada para
cierre por el Reviewer.

Fase 7A usa un job separado `Playwright E2E CI`, ejecutable sólo mediante
`workflow_dispatch`, con PostgreSQL E2E local, Chromium headless y datos
sintéticos. No se habilita trigger de PR, no se modifica el Ruleset y no se
publican traces, screenshots ni HTML reports; ante fallo sólo se permiten logs
sanitizados de API, frontend y PostgreSQL. Las fases 7B y 7C son posteriores.

La validación manual sobre `feature/mvp` quedó registrada en el run
`32598856151`, commit `a2124ff`: Chromium, PostgreSQL E2E, Alembic, seed,
API y frontend completaron correctamente; las tres specs produjeron
`3 passed (4.2s)`. El cleanup fue correcto y no se subieron logs al no haber
fallo. Playwright CI sigue siendo informativo y no required.

Para Fase 7B se habilita el job también en `pull_request` hacia `main`, sin
`pull_request_target`, sin filtros de paths y conservando `workflow_dispatch`.
La concurrencia se limita al job Playwright y cancela sólo ejecuciones
obsoletas del mismo PR. El Ruleset permanece sin cambios; la evaluación de
required queda reservada para Fase 7C.

La validación controlada de 7B quedó registrada en el PR #6, reconciliado con
`main`, mediante el run `32600285274` con evento `pull_request`. El PR fue
`MERGEABLE/CLEAN`; Backend CI, PostgreSQL CI, Frontend CI y Playwright E2E CI
terminaron correctamente, y Playwright produjo `3 passed (4.7s)`. El PR se
cerró sin merge. El PR #5 se conserva como antecedente: no ejecutó checks por
conflicto de merge. La concurrencia queda configurada, pero no fue validada
empíricamente mediante cancelación. Esta evidencia cierra Fase 7B; la
evaluación de Fase 7C queda pendiente hasta completar el umbral de estabilidad
definido.

## DEC-014 — Structured data SEO prerenderizado

Tipo: convención SEO implementada en el frontend.

El prerender genera un único JSON-LD `@graph` por página con referencias
`@id` estables para Organization y WebSite, y WebPage enlazada al canonical.
Las landings comerciales agregan SoftwareApplication; las breadcrumbs y
FAQPage se limitan a rutas/contenido donde existen. Las respuestas FAQ
reutilizan los datos de sus acordeones. No se agrega Product, rating, review,
precio ni oferta estructurada sin datos verificables.

## DEC-015 — Autorización administrativa separada para Consultorio

Tipo: diseño de seguridad integrado en `main`.

`ConsultorioAdministrador` concede administración sólo del dominio de espacios del Consultorio y no deriva permisos desde `CuentaUsuario`, del rol de propietaria ni de `ConsultorioProfesional`. La relación profesional-consultorio conserva el `Profesional.cuenta_id` individual. No crea permisos clínicos compartidos. La migración es aditiva; su downgrade se rehúsa mientras haya configuración de Consultorio persistida para evitar pérdida silenciosa.

## DEC-016 — Recurrencias de módulos y reserva exclusiva de sala

Tipo: decisión funcional aprobada e integrada en `main` mediante Entrega 03.

Una regla semanal define hora civil en la zona IANA del consultorio y una versión efectiva desde fecha futura. La expansión genera ocurrencias idempotentes en horizonte móvil de 90 días; la consulta administrativa o una reserva extiende el horizonte en su propia transacción. PostgreSQL es la autoridad final para excluir intervalos activos superpuestos por sala con rango `[inicio, fin)` y mantener adyacencias válidas. Las reglas concurrentes se serializan bloqueando la sala; la generación se serializa por regla y fecha civil es clave única. El cambio de profesional o sala desde una fecha crea una serie nueva y preserva la anterior. Cambios/suspensiones con turnos reservados/confirmados se bloquean con conteo agregado, sin datos de paciente ni cambios automáticos. Alta/reprogramación de turnos vinculados deben caber íntegramente en módulo vigente y disponibilidad propia; el profesional sin vínculo conserva el flujo individual.

## DEC-017 — Invitación previa a cuenta, plaza y módulos

Tipo: diseño funcional y de seguridad integrado en `main` mediante PR #90; no desplegado.

La propietaria prepara una invitación con email normalizado y reglas semanales antes de enviarla. La invitación y sus ocurrencias reservan plaza y sala sin crear identidad profesional ficticia. Series y ocurrencias tienen exactamente un destino: profesional o invitación; las ocurrencias pendientes siguen activas bajo la exclusión GiST. El cupo configurable cuenta perfiles activos distintos, incluida la titular, más invitaciones no vencidas, con bloqueo de la fila consultorio. Los valores iniciales son cuatro plazas y siete días.

El token de alta entropía persiste sólo como hash; el enlace lo transporta en el fragmento del navegador. Reenvío rota el hash, revocación/vencimiento lo invalida y la aceptación exige JWT, perfil profesional existente y email verificado coincidente. La aceptación se ejecuta en transacción y puede repetirse por el mismo usuario sin duplicar el vínculo. El invitado sin cuenta sigue el registro individual en otra pestaña y vuelve a la invitación; no existe handoff server-side. El alta individual actual requiere matrícula y especialidad. No se transfieren cuentas ni permisos clínicos y la administradora no obtiene agendas/pacientes ajenos.

## DEC-018 — Panel de ocupación sin información clínica

Tipo: diseño de interfaz y autorización preparado en la rama `codex/consultorio-05-panel-administrativo`; no desplegado.

El panel de administración usa la misma sesión profesional, conserva el shell de Turnelia y se muestra desde la navegación sólo cuando `GET /consultorios` devuelve consultorios administrados. La condición visual no concede autorización: backend vuelve a resolver `ConsultorioAdministrador` en cada lectura y mutación. Los endpoints mínimos de profesionales y reglas semanales devuelven campos allowlist para operar el panel. La agenda muestra únicamente sala, intervalo, estado y profesional asignado o el rótulo genérico “Invitación pendiente”; no propaga nombre/correo de la invitación ni datos clínicos. En modo Consultorio el shell omite notificaciones profesionales. La UI muestra sólo `turnos_afectados` ante un bloqueo y no modifica automáticamente turnos. No requiere migración ni cambia membresías o suscripciones.


## DEC-019 — Actividad profesional y matrícula condicional (Entrega 06)

Tipo: decisión funcional aprobada e implementación en revisión.

Las reglas de matrícula y especialidad provienen del catálogo servidor `ActividadProfesional`, nunca del rol ni de banderas enviadas por el cliente. El alta nueva debe elegir una actividad; perfiles anteriores mantienen `actividad_profesional_id=NULL` y conservan sus valores y relaciones sin inferencia. Servicios de estética usan la especialidad de servicio existente configurada en el catálogo para seguir siendo compatibles con prestaciones y turnos sin pedir matrícula. Clasificar un perfil heredado como actividad sin matrícula requiere borrar explícitamente su matrícula histórica. La migración Alembic `a7b8c9d0e1f2` es aditiva; el downgrade se detiene ante datos que no puede representar. No valida la autenticidad de matrícula contra registros externos.

## DEC-020 — Preproducción separada de producción

La Entrega 07 prepara `docker-compose.staging.yml` como proyecto Compose `turnelia-staging`, con DB privada, redes y volúmenes propios, loopback para API/frontend, noindex y analítica desactivada. Secretos sintéticos se generan a un archivo externo que no se sobrescribe. El seed exige ambiente/base específicos y usa identidades sintéticas. Las pruebas de backup y restore usan exclusivamente la DB staging. No se añade Caddy/proxy ni se habilita correo/WhatsApp real por defecto. La preparación remota queda pendiente mientras no pueda inspeccionarse el VPS con acceso de sólo lectura.
