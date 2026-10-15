# Entrega 06 — Actividad profesional y matrícula condicional

Estado: **IMPLEMENTACIÓN COMPLETA — PR ABIERTO, CI VERDE**
Base: `origin/main` en `40e8c36a77f59f7e7eb6c35b00bc61f74b4414cc`
Rama: `codex/consultorio-06-actividad-matricula`

## Objetivo

Permitir alta y mantenimiento del perfil según un catálogo controlado de actividades. El backend resuelve desde ese catálogo si hacen falta matrícula y especialidad; el rol profesional y los campos enviados por el cliente nunca determinan las reglas. Se mantiene intacto el ownership clínico y el flujo actual de cuentas individuales.

## Diseño técnico

- Añadir `ActividadProfesional`, catálogo persistente con clave estable, nombre visible, indicador de matrícula requerida, indicador de especialidad requerida, especialidad de servicio predeterminada opcional y estado activo. Los indicadores son configuración confiable del servidor, no campos editables por el profesional.
- Sembrar en Alembic dos opciones iniciales: actividad profesional matriculable (requiere matrícula y especialidad, que selecciona del catálogo existente) y servicios de estética (sin matrícula ni especialidad solicitadas; el servidor asocia la categoría de servicio existente “Estética” para conservar el flujo de prestaciones y turnos).
- Asociar `Profesional.actividad_profesional_id` como nullable y cambiar `matricula` a nullable. No asignar actividad ni modificar matrícula a perfiles heredados; actividad nula significa “pendiente de clasificación”, no una inferencia. La matrícula histórica se conserva.
- Para altas nuevas, exigir `actividad_profesional_id`; derivar los campos permitidos/obligatorios del catálogo en el servicio. Actividad matriculable exige matrícula no vacía y especialidad existente/activa. Estética rechaza matrícula inventada/vacía enviada explícitamente y resuelve su categoría configurada en backend.
- Las modificaciones propias permiten cambiar actividad sólo si el nuevo conjunto cumple sus requisitos. No existe ruta que permita editar perfiles ajenos al usuario profesional autenticado. Administradores que usen el alta administrativa deben seleccionar actividad y cumplir las mismas reglas.
- Exponer un catálogo público mínimo (id, código, nombre y requisitos de formulario) sin permitir modificar reglas. Perfil propio muestra actividad y matrícula sólo cuando corresponda; perfiles heredados sin clasificación se identifican como pendientes sin alterar sus datos.
- La migración es aditiva y reversible con guardas: downgrade se rehúsa si hay perfiles clasificados o matrículas nulas, porque perdería configuración o no podría restaurar NOT NULL. No se modifica información clínica ni se clasifican perfiles automáticamente.

## Compatibilidad y seguridad

- Los perfiles existentes conservan propietario, cuenta, matrícula, especialidades, prestaciones, turnos y registros clínicos; la nueva clave queda nula hasta clasificación explícita.
- El perfil heredado sigue usando sus relaciones y su matrícula histórica. Puede editar campos de contacto/especialidades propios; no se exige una clasificación retroactiva para iniciar sesión ni agendar.
- Clasificar un perfil heredado como actividad sin matrícula exige que la petición incluya `matricula: null`; el servidor no borra una matrícula histórica implícitamente. Para una actividad sin especialidad, la categoría de servicio predeterminada se asigna desde el catálogo. El cambio de categoría comprueba dependencias con prestaciones antes de reemplazar especialidades.
- Ningún requisito se toma del body: se consulta el catálogo en backend para alta y actualización. Los schemas rechazan propiedades de política. Errores de ownership permanecen 403/404 conforme al contrato actual.
- El catálogo no concede permisos sobre pacientes, agenda, documentación clínica ni Consultorio. No se añaden campos de actividad a APIs públicas de pacientes o perfiles de terceros.
- La categoría de servicio “Estética” ya existe en el catálogo de especialidades integrado en `main`; asociarla permite crear prestaciones/turnos existentes sin pedir matrícula ni declarar una especialidad/matrícula falsa.

## Etapas incrementales

### 06A — Baseline y contratos

1. Confirmar `origin/main`, estado Git y rama; preservar `docs/audits/`.
2. Registrar la línea base con `verify.ps1 -Full`, estado de E2E y PostgreSQL disponible.
3. Agregar pruebas de reglas de catálogo, migración heredada y ownership antes de ampliar UI.

### 06B — Dominio y API

1. Modelo, schema allowlist, repository/service/router y catálogo de sólo lectura.
2. Validación condicional de registro, alta administrativa y edición propia.
3. Migración Alembic aditiva/reversible; pruebas SQLite, HTTP negativas y PostgreSQL real desechable.

### 06C — Registro, onboarding y perfil

1. Selección accesible de actividad en registro; matrícula/especialidad aparecen según reglas del catálogo.
2. Onboarding reutiliza la actividad asignada, conserva compatibilidad de perfiles heredados y no inventa datos.
3. Perfil propio presenta actividad/matrícula conforme a requisitos, sin exponer información clínica ajena.
4. Vitest/RTL para estados, validación y accesibilidad; Playwright sintético para registro estético y matriculable.

### 06D — Documentación y gate

1. Actualizar arquitectura, seguridad, pruebas, estado, decisiones y roadmap.
2. Ejecutar pytest, PostgreSQL, Vitest, lint/build, `verify.ps1 -Full`, `verify.ps1 -E2E` y `git diff --check`.
3. Revisar compatibilidad/seguridad, commit, push, PR a `main` y esperar Backend, PostgreSQL, Frontend y Playwright CI verdes.
4. No mergear ni desplegar.

## Criterios de aceptación

- Registro de actividad matriculable rechaza matrícula vacía o faltante y especialidad faltante/inactiva.
- Registro de estética crea perfil sin matrícula ni input de especialidad, sin valores ficticios; usa la categoría de servicio configurada por backend.
- Otro usuario no puede editar actividad, matrícula, especialidad ni otros datos del perfil.
- Perfil previo sin actividad se preserva y sigue autenticándose/operando; no recibe clasificación automática.
- La migración completa y downgrade de base vacía pasan en PostgreSQL. Downgrade con perfiles nuevos protegidos aborta sin pérdida de datos.
- No hay regresión de reserva pública, prestaciones, invitaciones ni aislamiento clínico.
- Checks locales y CI requeridos quedan verdes antes del PR final.

## Registro de evidencia

- Preflight: `origin/main` actualizado a `40e8c36a77f59f7e7eb6c35b00bc61f74b4414cc`; rama creada desde ese commit.
- Árbol preexistente: `docs/audits/` no versionado, conservado fuera del alcance.
- Línea base `verify.ps1 -Full`: backend terminó sin errores visibles; Vitest falló en dos pruebas ajenas a esta entrega (`agendaProfesionalIntegracion.test.tsx` timeout de 5 s y `cuentasAdmin.test.tsx` no encontró botón “Siguiente” antes de terminar de cargar). Lint y build pasaron. E2E no se ejecuta en modo Full. Repetir suites al final para distinguir flakiness de regresión y registrar conteos completos.
- Implementado: modelo y catálogo persistente; migración `a7b8c9d0e1f2`; alta pública, alta administrativa, edición propia, onboarding y presentación del perfil; UI condicional; pruebas backend y Vitest; E2E sintético; CI incluye el módulo PostgreSQL y el spec Playwright.
- Pruebas focalizadas: 37 backend aprobadas; 17 Vitest aprobadas; lint/build aprobados.
- Validación final: `verify.ps1 -Full` verde (backend, Vitest, lint y build; E2E omitido por el propio modo Full). Pytest directo: 912 passed, 39 skipped, 9 warnings. Vitest directo: 415 passed en 52 archivos. PostgreSQL 17 desechable: Alembic upgrade → downgrade a `c04inv202610` → upgrade head pasó; prueba del catálogo, FK y nulabilidad pasó 1/1. Playwright aislado con PostgreSQL y datos sintéticos: 12 passed, cleanup correcto. Se amplió el timeout de test de 5 a 15 segundos y de consultas Testing Library a 3 segundos para evitar expiraciones intermitentes preexistentes; no se debilitó ninguna assertion funcional.
- Primer CI del PR #92 detectó que la prueba PostgreSQL de actividad dependía de filas en la base compartida del job; se cambió para crear una base PostgreSQL efímera, ejecutar allí la cadena Alembic completa y eliminarla al finalizar. No era un fallo de la migración, sino de aislamiento de la prueba.
- PR #92: `https://github.com/luquemariano/mediturnos/pull/92`. Segundo CI (`Turnelia CI`, run `38778506901`, commit `1dc2088e8749640f292bb74e27fded0877aa9c19`): Backend, PostgreSQL, Frontend y Playwright E2E completados con `success`. PR abierto, sin merge ni despliegue.
