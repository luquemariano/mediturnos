# Entrega 04 — Invitaciones y vinculación controlada

Estado: **IMPLEMENTACIÓN COMPLETADA; PR/CI PENDIENTES**
Depende de: Entrega 03, integrada en `main` como `983f34f`.
Alcance: invitar, aceptar y vincular profesionales sin ampliar permisos clínicos ni activar cobros, producción o membresías múltiples comerciales.

## Objetivo

Permitir que Valentina reserve una plaza y los módulos de una persona antes de invitarla. La persona podrá aceptar usando una cuenta profesional existente o crear una nueva. Al aceptar, conserva su cuenta y perfil profesional individuales y queda vinculada operativamente al consultorio con sus horarios ya asignados.

## Reglas obligatorias

- Máximo inicial configurable de cuatro plazas activas o pendientes por consultorio; la titular cuenta dentro del cupo. Una invitación pendiente reserva una plaza.
- Invitación por email y enlace de un solo uso. El token se genera criptográficamente, se almacena sólo como hash, nunca se registra en logs ni respuestas persistidas.
- Vencimiento por defecto configurable de siete días; revocación y reenvío invalidan el enlace anterior. Aceptación/reintento es idempotente.
- El email aceptante debe coincidir con el email normalizado invitado y estar verificado según el flujo existente. No revelar si un email existe en Turnelia.
- La administradora prepara identidad mínima no clínica y los módulos antes de enviar. Si la persona todavía no tiene perfil, las reservas de sala deben persistir como asignación pendiente dentro del mismo mecanismo de exclusión de sala; no crear cuentas, perfiles, pacientes, matrículas ni datos ficticios.
- Al aceptar, el backend convierte atómicamente la asignación pendiente al profesional autenticado y activa el vínculo, revalidando cupo, expiración, revocación, sala y ausencia de solapamientos.
- Una asignación pendiente nunca permite crear, reservar ni reprogramar turnos. Sólo un profesional vinculado puede usar sus propios módulos.
- La propietaria no obtiene agenda ajena ni datos clínicos. Las respuestas administrativas no incluyen pacientes, turnos, evoluciones, documentos ni identidad clínica.
- No implementar transición de suscripciones, precios, Mercado Pago, envío real de correos, despliegue ni migración productiva.

## Diseño y migración

Agregar una migración Alembic aditiva para invitaciones y reservas pendientes, compatible con PostgreSQL:

- `InvitacionConsultorio`: consultorio, email normalizado, nombre visible opcional, hash de token, invitante, estado, vencimiento, consumo/revocación y auditoría.
- Un mecanismo explícito para vincular módulos pendientes a una invitación sin `profesional_id`, con checks que exijan exactamente un destino (profesional activo/preparatorio o invitación pendiente) y sin debilitar la exclusión GiST de sala.
- La aceptación reemplaza la asignación pendiente por el profesional autenticado de forma transaccional, conservando la ocupación de sala y el historial.
- El límite de plazas se cuenta con bloqueo/concurrencia; no se debe confiar sólo en un conteo previo.
- El downgrade debe proteger datos de invitaciones/asignaciones existentes.

Inspeccionar primero los modelos y constraints de Entrega 03. Adaptar los nombres si la opción mínima segura difiere, pero preservar las reglas anteriores y documentar la decisión.

## API y seguridad

Mantener `router → service → repository`.

- Administración del consultorio propio: preparar invitado y módulos pendientes, crear/listar/revocar/reemitir invitaciones sin token plano.
- Flujo público/autenticado de consulta y aceptación por token: mensajes no enumerables, token inválido/expirado/revocado tratado de manera uniforme.
- Cuenta existente: aceptación sólo para el profesional autenticado cuyo email coincide.
- Cuenta nueva: continuar mediante el alta profesional existente sin transportar token en logs; completar aceptación autenticada al finalizar. Si el flujo actual no permite un handoff seguro, implementar sólo un enlace corto de sesión/estado firmado y de un uso, sin secretos en URL persistidos, o documentar el bloqueo en vez de inventar credenciales.
- Un profesional puede leer solamente sus módulos ya activos; no puede aceptar invitación ajena, administrar invitados, cambiar módulos ni crear turnos en reservas pendientes.
- La administradora puede ver estado agregado de invitación/cupo y ocupación de sala, nunca información clínica.

## Etapas

### 04A — Contratos y amenazas

1. Relevar alta/inicio de sesión/verificación de email, roles, perfiles profesionales y modelos de Entrega 03.
2. Definir el flujo de cuenta existente y nueva sin enumeración de email ni token plano.
3. Añadir contratos y pruebas negativas de permisos, token, expiración, revocación, email ajeno y ausencia de datos clínicos.

### 04B — Persistencia y concurrencia PostgreSQL

1. Implementar modelos y migración Alembic aditiva, índices, checks y relaciones.
2. Conservar exclusión GiST para módulos pendientes y activos en una misma sala.
3. Probar aceptación concurrente, cupo concurrente, token de un uso, revocación frente a aceptación y downgrade protegido sobre PostgreSQL real.

### 04C — Servicios y endpoints

1. Implementar preparación de invitado/módulos, emisión, revocación/reenvío y listado administrativo seguro.
2. Implementar aceptación idempotente para cuenta existente; integrar el handoff seguro para cuenta nueva si el flujo existente lo permite sin riesgo.
3. Activar la relación operativa y las asignaciones sólo tras validaciones transaccionales. Mantener bloqueados los turnos de asignaciones pendientes.

### 04D — Gate y documentación

1. Ejecutar suites backend, PostgreSQL, frontend, lint/build y Playwright acordadas; agregar E2E sintético de invitación/aceptación cuando sea proporcionado.
2. Actualizar arquitectura, seguridad, testing, estado, decisiones, roadmap y este plan.
3. Crear commit, push y PR hacia `main`; esperar CI verde. No hacer merge, deploy ni migraciones productivas.

## Fuera de alcance

- Panel visual final, calendario consolidado, agenda de terceros y datos clínicos compartidos.
- Suscripciones, planes, cobros, Mercado Pago y transición comercial.
- Actividades sin matrícula, cambios de precios y uso con datos reales.
- Correos reales, despliegue o migración de producción.

## Criterio de cierre

La entrega se considera lista para revisión sólo con cupos y sala protegidos bajo concurrencia, enlaces no reutilizables ni filtrables, aceptación que conserva la identidad profesional, módulos pendientes que no permiten turnos y aislamiento clínico intacto.

## Registro de implementación

- **04A:** el registro individual existente requiere matrícula y especialidad, crea cuenta/suscripción individual y verifica email por separado. El enlace de invitación mantiene su token sólo en memoria y en el fragmento de la URL; un invitado nuevo abre el registro en otra pestaña, verifica y vuelve al enlace. No se añade handoff persistente.
- **04B:** revisión Alembic `c04inv202610`, aditiva y PostgreSQL-only; agrega cupo/expiración configurables, invitación y destino nullable exclusivo en series/ocurrencias. No se modifica el predicado GiST; las reservas pendientes son `activas`. El downgrade rehúsa revertir con invitaciones o destinos pendientes persistidos.
- **04C:** preparación/listado/envío/reenvío/revocación y aceptación; se actualizan vínculo y destinos en transacción. Los turnos sólo buscan ocurrencias con `profesional_id` asignado.
- **Pruebas añadidas:** HTTP/SQLite para hash, respuesta administrativa sin token, rotación, aceptación idempotente, email distinto, revocación, cupo y control administrativo; PostgreSQL real para cupo concurrente y exclusión GiST de invitación pendiente.
- **Límite de alta nueva:** no se persiste token de handoff; si se cierra la pestaña original se puede volver a abrir el enlace del correo, salvo que haya sido revocado o reenviado. El formulario individual actual requiere matrícula y especialidad, por lo que altas sin esos requisitos permanecen fuera de alcance.
- **04D local:** `pytest -q`: **900 passed, 38 skipped** (suites PostgreSQL opcionales omitidas en esta ejecución SQLite); PostgreSQL CI completo: **35 passed, 0 skipped**; Vitest: **51 archivos, 408 passed**; lint y build frontend: **OK**; Playwright Chromium/PostgreSQL sintético: **8 passed**; `git diff --check`: ejecutar antes del commit. Playwright limpió su proyecto/volumen temporal y se restauraron las capturas documentales generadas.
- **Pendiente de cierre remoto:** commit, push, creación/actualización del PR y CI verde. No se envió correo real ni se ejecutaron cobros, migraciones productivas o despliegues.
