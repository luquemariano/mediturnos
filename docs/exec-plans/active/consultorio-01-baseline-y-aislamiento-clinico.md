# Consultorio 01 — línea base y aislamiento clínico

Estado: **IMPLEMENTADO — CI verde; PR abierto para revisión**
Prerequisito funcional: Fase 0 aprobada en [`../../PLAN_CONSULTORIO.md`](../../PLAN_CONSULTORIO.md).
Fecha del plan: **2026-10-14**.

## Objetivo

Registrar una línea base reproducible de las suites y corregir/clasificar los fallos anteriores de forma acotada. Después, hacer que todo acceso profesional a perfiles clínicos, evoluciones, documentos y estudios se filtre por el profesional propietario. Conservar registros cuyo owner sea demostrable y restringir/revisar los ambiguos.

Esta entrega es un gate de seguridad previo a habilitar cuentas multi-profesional, invitaciones aceptadas o acceso del panel consultorio a datos de miembros. No agrega el panel, salas, recurrencias ni cobros.

## Contexto verificado

- La auditoría local [`../../audits/AUDITORIA_VALENTINA_2026-10.md`](../../audits/AUDITORIA_VALENTINA_2026-10.md) reportó: pytest 872 pasados, 26 omitidos, 1 fallo por fecha; Vitest 406 pasados y 1 timeout que pasó al repetirlo aislado; Playwright 4/7, con un fixture que no completa verificación de email y dos expectativas de ayuda desactualizadas.
- `EvolucionClinica` ya tiene `profesional_id`, pero el listado profesional filtra sólo por paciente.
- `ClinicalProfile` hoy es único por paciente y conserva `updated_by_profesional_id`, no un owner explícito.
- `PatientDocument` conserva `uploaded_by_profesional_id`, pero listas/descargas profesionales se consultan por paciente. Las cargas del paciente ligadas a `StudyRequest` no tienen uploader profesional y deben heredar el profesional de la solicitud.
- `StudyRequest` y `StudyReview` incluyen `profesional_id`; sus joins, respuestas y documentos asociados deben mantener esa frontera.
- El estado Git al inicio de esta fase documental tenía cambios de documentación del Plan Consultorio y `docs/audits/` sin seguimiento preexistente; preservar los archivos ajenos al implementar.

## Alcance

1. Capturar versiones/entorno y repetir validaciones existentes para una línea base actual, sin mutar producción. Marcar cada falla como reproducida, intermitente o no reproducida y conservar sólo logs sanitizados.
2. Corregir sólo la prueba dependiente de fecha, el timeout Vitest, el fixture E2E de email y las expectativas de ayuda si siguen fallando. No elevar timeouts ni cambiar aserciones para ocultar problemas sin aislar causa.
3. Mapear ownership clínico y query paths de API, storage y tokens de estudios.
4. Añadir ownership explícito por profesional al perfil clínico y a documentos donde hoy no existe. Cambiar filtros de servicios/repositorios para que el `profesional_id` autenticado sea parte de la consulta, no una validación posterior sobre filas globales.
5. Mantener `EvolucionClinica.profesional_id` como autor/owner y limitar listados/mutaciones profesionales al valor de sesión.
6. Backfill únicamente desde evidencia consistente: perfil desde `updated_by_profesional_id` con vínculo profesional-paciente verificable; documento desde `StudyRequest.profesional_id`, o desde `uploaded_by_profesional_id` cuando no tenga solicitud y la relación sea válida.
7. Filas sin owner verificable conservan el contenido pero quedan con owner nulo/estado restringido, fuera de respuestas profesionales y propietarios del consultorio, hasta revisión explícita. No duplicarlas entre vínculos del paciente. La vista administrativa existente conserva sólo su autorización global actual; no concederla al propietario de cuenta.
8. Activar el filtro en rutas de perfil, evolución, documentos, solicitud/revisión y carga/lectura pública de estudios; preservar URL firmada/autogestión con el request ID validado contra paciente y profesional.

## Fuera de alcance

- Crear cuenta organizacional, membresías, invitaciones o aceptar profesionales.
- Reglas recurrentes, ocurrencias de sala, turnos de consultorio o pantallas nuevas.
- Cambiar cuentas/suscripciones individuales, precios, cobros o proveedor de pagos.
- Revisar o reasignar contenido clínico productivo; el primer backfill se valida sobre copia sanitizada.
- Resolver la alerta de dependencias de producción salvo que la línea base revele que bloquea un gate de seguridad; dejarla como trabajo separado.

## Secuencia incremental

### 01A. Línea base reproducible

1. Leer los comandos vigentes de `docs/TESTING.md` y capturar commit, Python/Node, navegador/Docker disponibles y variables presentes sin imprimir sus valores.
2. Ejecutar backend completo (`python -m pytest`), Vitest (`npx vitest run tests`), lint, build y E2E (`verify.ps1 -E2E`) en su entorno aislado si está disponible. No combinar `-LocalServices` con E2E ni acceder a producción.
3. Registrar conteos, duración, skips y fallos; comparar con la auditoría. Separar fallos de baseline en cambios pequeños del código de aislamiento para que la revisión pueda distinguir regresiones.

### 01B. Contratos de aislamiento y pruebas negativas

1. Crear fixture con dos profesionales y el mismo paciente enlazado a ambos, más un propietario de consultorio sin perfil profesional.
2. Probar lectura y escritura permitida del profesional dueño; denegar a B todos los IDs de A, incluso cuando B conoce `paciente_id`, `document_id`, `request_id` o un token válido de su propia solicitud.
3. Cubrir propietario de cuenta, miembro y administrador global por separado: pertenecer a cuenta consultorio no cambia el rol clínico; sólo se conservan privilegios globales existentes.
4. Escribir pruebas antes del cambio de consulta. Revisar que no haya datos parciales, URLs de storage ni nombres/prestaciones de otro profesional en respuestas de error.

### 01C. Modelo, migración y filtros

1. Evoluciones: mantener owner existente y añadir filtros por `paciente_id` + `profesional_id` en listado; escritura comprueba ownership/vínculo.
2. Perfil: añadir `profesional_id` nullable inicialmente, migrar perfiles con autor verificable, reemplazar unicidad por paciente por unicidad `(paciente_id, profesional_id)` para filas asignadas y restringir perfiles nulos. Consultas y upsert operan por pareja.
3. Documentos: añadir `profesional_id` nullable; backfill por solicitud o uploader validado; crear con owner de la sesión o solicitud. Listado, endpoint por solicitud, confirmación, download URL, borrado, upload intent y public upload consultan propietario.
4. Estudios: asegurar que request, review, documentos y paciente coinciden; impedir que un usuario profesional resuelva un request ajeno por cambiar IDs en la ruta.
5. Crear migración Alembic aditiva compatible con PostgreSQL. No hacer drop de datos; verificar FKs, índices únicos/parciales y compatibilidad SQLite, conteos de antes/después y downgrade seguro para campos nuevos.
6. Hacer backfill reanudable con conteos de control. El mecanismo de restricción para filas ambiguas usa owner nulo/estado explícito; ningún endpoint profesional las devuelve. La activación de invitaciones multi-profesional queda detrás de un gate/feature flag hasta completar pruebas y revisión.

### 01D. Revisión y gate

1. Ejecutar pytest focalizado y completo; Vitest, lint/build; PostgreSQL CI con migración desde base vacía y tests de aislamiento; Playwright E2E autenticado.
2. Revisar diff con enfoque de ownership, enumeración de IDs, almacenamiento y datos sensibles en logs. Usar Builder → Reviewer documentado.
3. Cerrar sólo si A y B ven registros clínicos distintos del mismo paciente, todos los ataques cruzados fallan, los casos propios siguen funcionando, filas ambiguas no salen en APIs profesionales y las suites/gates quedan en estado conocido.
4. No activar miembros múltiples en este PR. Esa capacidad espera las entregas posteriores del plan principal.

## Pruebas requeridas

### Backend/API

- `tests/test_clinical_profiles.py`: perfiles de A y B independientes; GET/PUT cruzados denegados por ID; B no sobrescribe perfil de A.
- `tests/test_evoluciones_clinicas.py`: listado sólo incluye `profesional_id` autenticado; creación exige vínculo propio; propietario sin perfil profesional no puede listar ni crear.
- `tests/test_patient_documents.py`: lista, upload intent, confirm, download URL y delete filtran owner; mismo paciente enlazado a B no concede acceso.
- `tests/test_patient_study_uploads.py`, `tests/test_study_reviews.py`, `tests/test_pending_study_reviews.py`, `tests/test_study_access_http.py`: carga pública por token acotada a solicitud/paciente; sólo el profesional de la solicitud lista/revisa; ID y token cruzados denegados.
- Revisar `tests/test_admin_cuentas.py` para demostrar que el rol de cuenta/consultorio no hereda acceso global.
- Crear módulos PostgreSQL de ownership/concurrencia y backfill de migración; agregarlos al job CI. Usar datos sintéticos y garantizar cleanup.

### Frontend/E2E

- Vitest mantiene panel profesional actual y verifica que las pantallas sólo soliciten los datos clínicos propios.
- Playwright con A, B y propietaria: A crea datos clínicos; B y propietaria intentan abrir vistas/endpoints con IDs conocidos; no aparece contenido ni metadata clínica; A mantiene acceso.
- Corregir el 403 del fixture con email verificado para que la sesión E2E represente el flujo permitido. No usar emails ni pacientes reales.

## Riesgos y reversión

- **Perfil actual único por paciente:** migrar a ownership profesional puede revelar registros sin autor. Conservarlos en estado restringido; revisión humana posterior y registro de quién asigna ownership.
- **Documentos de pacientes:** owner debe heredarse de la solicitud, nunca de quién mira ni de `paciente_id`; tokens se validan contra solicitud y paciente en cada acción.
- **Storage:** denegar metadata y URL firmada de documentos no propios, incluso si la key sigue válida. No cambiar físicamente objetos en R2/fake durante la migración.
- **SQLite/PostgreSQL:** Alembic desde PostgreSQL vacío es gate; índices parciales, FKs y constraints se comprueban en ambas configuraciones admitidas.
- **Rollback:** desactivar feature flag y volver a rutas anteriores sólo tras preservar owner agregado; no eliminar columnas ni filas restringidas. La corrección de filtros es permanente y una reversión de código no puede volver a exponer registros ajenos.
- **Datos reales:** no ejecutar backfill ni abrir pacientes reales en esta entrega. Estimar filas ambiguas sólo en copia sanitizada; un despliegue requiere autorización y procedimiento separado.

## Bloqueos efectivos

No queda decisión funcional del propietario pendiente para iniciar esta entrega. Ya está aprobada la política de conservar owner inequívoco y restringir owner ambiguo.

La aceptación sí depende de repetir la línea base, verificar sobre copia sanitizada qué owners son demostrables y pasar pruebas negativas de backend/PostgreSQL. Mientras cualquiera falle o carezca de evidencia, no se habilitan invitaciones/miembros múltiples. Catálogo de actividades, términos comerciales de alquiler, transición de suscripciones, WhatsApp real y restauración de backup pertenecen a entregas posteriores y no detienen este primer plan.

## Validación de este plan

### Implementación y evidencia (2026-10-14)

- **01A — línea base:** backend inicial `872 passed, 26 skipped, 1 failed`; la falla por fecha en `test_admin_adoption.py` se estabilizó con reloj congelado sólo en el test. Final: `878 passed, 28 skipped, 9 warnings` (`pytest -q -ra`). Los skips restantes son pruebas que requieren PostgreSQL opcional.
- **01B — aislamiento:** añadidas pruebas negativas de perfil, evolución, solicitud y documentos; Playwright ejercita dos profesionales sobre el mismo paciente sintético. El panel administrativo no recibe datos clínicos de pacientes.
- **01C — modelo/migración:** perfiles y documentos reciben `profesional_id` nullable con FK e índice; el backfill atribuye sólo con evidencia consistente. La prueba Alembic en base PostgreSQL temporal recorre desde la revisión anterior, confirma perfiles y documentos atribuidos por vínculo, uploader o solicitud, conserva owner nulo en filas ambiguas y demuestra que el downgrade falla si existen perfiles separados. No se ejecutó contra producción ni datos reales.
- **01D — revisión:** la revisión independiente no halló rutas actuales de acceso cruzado. Señaló falta de evidencia automatizada de backfill, ya cubierta por la prueba nueva. Observación residual: un documento inconsistente con el profesional de su `StudyRequest` queda inaccesible para revisión; el flujo actual escribe ambos owners de forma consistente.
- **Backend:** `878 passed, 28 skipped, 9 warnings`; sin fallos.
- **PostgreSQL 17:** migración completa desde base vacía y ambos módulos PostgreSQL nuevos `2 passed, 0 failed` en la misma ejecución CI-like; la prueba de migración crea/elimina su propia base sintética temporal. SQLite no valida la cadena heredada: una migración previa usa `create_foreign_key` sin batch y falla antes de esta revisión.
- **Frontend:** lint y build correctos; SSR y prerender generaron 22 rutas. Vitest completo terminó `407 passed, 0 failed` en la repetición; en el intento anterior hubo un fallo de carga en `adminAdoption.test.tsx` (406/407), y la repetición focalizada dio `3 passed, 0 failed`. No se aumentaron timeouts ni se ocultó el primer resultado.
- **Playwright:** `verify.ps1 -E2E`, PostgreSQL y cuentas/pacientes sintéticos; `8 passed, 0 failed`, cleanup completado. Capturas dirigidas a `frontend/test-results/consultorio-01/screenshots`, no a assets versionados.
- **Seguridad operativa:** el primer E2E expuso en logs locales un token sintético de estudio público por el access log de Uvicorn. Se desactivó access logging en el harness E2E; no se imprimieron credenciales reales y la configuración productiva no se cambió.
- **Git/CI:** rama `codex/consultorio-01-clinical-isolation`; PR #87 abierto. Backend, Frontend, PostgreSQL y Playwright CI pasaron; no se hizo merge, despliegue ni migración productiva.
- **Gate:** no habilitar cuentas multi-profesional. Los controles de esta entrega pasaron en local y CI. Antes de desplegar/backfillear datos, clasificar la copia sanitizada prevista y preparar revisión de filas ambiguas.
