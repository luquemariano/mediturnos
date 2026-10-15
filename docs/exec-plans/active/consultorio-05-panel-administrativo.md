# Entrega 05 — Panel administrativo y agenda consolidada

Estado: **IMPLEMENTACIÓN COMPLETA, EN REVISIÓN**
Depende de: Entregas 01–04 integradas en `main` como `f8b256c`.
Alcance: interfaz administrativa para la propietaria del consultorio, agenda consolidada de ocupación y operación visual de módulos e invitaciones. No despliega ni activa comercialmente el Plan Consultorio.

## Objetivo

Permitir que Valentina use su misma sesión de profesional para entrar a un panel de consultorio separado, consultar la ocupación de la sala y gestionar los módulos e invitaciones ya implementados en backend.

El panel muestra disponibilidad de espacio, no agenda clínica. Cada bloque identifica solamente sala, intervalo, estado y profesional asignado o invitación pendiente. Nunca muestra pacientes, prestaciones, turnos, contactos clínicos, evoluciones, documentos ni historias de terceros.

## Experiencia y estética

- Reutilizar componentes, tipografías, colores, navegación, espaciados, mensajes y patrones de accesibilidad existentes de Turnelia. No crear una identidad visual paralela ni introducir una librería visual grande sin necesidad.
- Integrar el acceso `Consultorio` sólo cuando el usuario autenticado administra al menos un consultorio. La cuenta de Valentina conserva su panel profesional habitual.
- Diseño usable en desktop y móvil; agenda semanal legible, con estados y leyenda accesibles sin depender sólo del color.
- Todo texto visible debe estar en español.

## Funcionalidad obligatoria

### Acceso y contexto

- Obtener los consultorios administrados para el usuario autenticado, con autorización en backend. Si falta una lectura mínima segura, agregarla manteniendo `router → service → repository`.
- No asumir que la persona propietaria es administradora global ni derivar permisos del frontend.
- Un profesional que no administra el consultorio no puede descubrir la ruta, datos ni acciones administrativas; el backend debe negar igualmente cualquier acceso directo.

### Agenda consolidada

- Vista semanal por sala, con navegación anterior/siguiente y regreso a la semana actual.
- Mostrar ocurrencias recurrentes, extraordinarias, suspendidas/canceladas y reservas pendientes de invitación dentro del rango.
- Diferenciar visualmente ocupada, pendiente y liberada; no exponer información clínica.
- Mostrar sólo la ocupación autorizada de la sala; no inferir ni mostrar huecos como turnos de pacientes.
- Los filtros de rango deben ser explícitos, con zona horaria del consultorio, y respetar el horizonte de materialización. Tratar datos inválidos/error de carga sin ocultar fallos.

### Gestión

- Crear reglas semanales para profesional ya vinculado y módulos extraordinarios mediante las APIs existentes.
- Suspender o modificar una ocurrencia/regla desde interfaz, confirmando la operación. Si backend devuelve `turnos_afectados`, explicar que la modificación queda bloqueada y sólo mostrar la cantidad, nunca pacientes.
- Preparar una invitación con email, nombre visible opcional y uno o más módulos semanales; listar estado, vencimiento y cantidad reservada.
- Enviar, reenviar o revocar una invitación con confirmación y feedback. Las pruebas deben simular proveedor; no enviar correos reales.
- No permitir al panel alterar suscripciones, precios, cobros, historias, pacientes, prestaciones ni agendas ajenas.

## API y contrato

- Reutilizar las APIs administrativas ya integradas cuando cubran el flujo.
- Si se agrega un endpoint para lista de administrados o lectura de profesionales vinculados, devolver sólo los campos mínimos para UI y filtrar siempre por usuario autenticado/consultorio administrado.
- No devolver tokens, hashes, enlaces de invitación, datos de paciente, documentos, evoluciones, ni conteos que permitan inferir datos clínicos.
- Mantener compatibilidad con módulos/invitaciones pendientes: una reserva pendiente es visible como ocupación, pero no se presenta como profesional activo.

## Pruebas

- Vitest/RTL: acceso condicional, carga, agenda, navegación semanal, estados, formularios y errores.
- Pruebas backend negativas si se añade lectura/contrato: otro profesional y un consultorio ajeno no pueden leer datos administrativos.
- Playwright con PostgreSQL aislado y fixtures sintéticos: Valentina ingresa al panel, ve ocupación sin datos clínicos, prepara y administra una invitación; un profesional no administrador es rechazado.
- No usar pacientes o correos reales. No probar la interfaz contra producción en esta entrega.

## Etapas

### 05A — Relevamiento y contratos

1. Inspeccionar navegación, diseño actual, APIs administrativas y modelos de Entregas 02–04.
2. Incorporar sólo las lecturas seguras que falten para panel/lista de administrados y profesionales aptos.
3. Añadir pruebas de autorización y DTOs mínimos.

### 05B — Panel y agenda

1. Crear la ruta/pantalla de Consultorio y acceso condicionado.
2. Implementar selector de consultorio y agenda semanal por sala.
3. Manejar estados, carga, vacíos, errores, accesibilidad y móvil conforme a estética existente.

### 05C — Operaciones visuales

1. Incorporar formularios/acciones de módulos recurrentes, excepciones y suspensiones.
2. Incorporar preparación, listado, envío/reenvío/revocación de invitaciones.
3. Respetar respuestas de bloqueo y no mostrar datos clínicos.

### 05D — Gate

1. Ejecutar backend, PostgreSQL, Vitest, lint/build, Playwright y `git diff --check`.
2. Actualizar arquitectura, seguridad, testing, estado, decisiones, roadmap y este plan.
3. Commit, push y PR hacia `main`; esperar CI verde. No hacer merge, despliegue, migración productiva, envío de correo real, cobro ni cambios de suscripción.

## Fuera de alcance

- Activación productiva del consultorio ALMA.
- Cambios de precios, suscripciones, Mercado Pago, migración comercial o múltiples salas comerciales.
- Directorio público, agenda consolidada de pacientes, información clínica compartida o edición de agendas ajenas.
- Nuevas reglas de matrícula/actividad.
- Pruebas contra producción.

## Criterio de cierre

La entrega queda lista para revisión cuando Valentina pueda, con su misma cuenta, administrar visualmente el consultorio y su ocupación sin acceder a datos clínicos de otros profesionales; el resto de profesionales conserva únicamente su panel y sus módulos propios.

## Evidencia de implementación local

- 05A–05D implementadas: dos lecturas administrativas allowlist, acceso condicional, panel responsive con agenda semanal, módulos e invitaciones.
- Pytest completo: 902 aprobados, 38 omitidos por suites PostgreSQL selectivas y 9 warnings preexistentes de deprecación/ORM.
- PostgreSQL 17 aislado: cadena Alembic completa y 10 pruebas Consultorio de concurrencia, exclusión y migración aprobadas.
- Vitest/RTL: 413 pruebas aprobadas; lint y build frontend aprobados.
- Playwright con PostgreSQL E2E aislado y proveedor `in_memory`: 10 pruebas aprobadas, incluyendo aislamiento, invitación y viewport móvil de 390 px sin desbordamiento horizontal.
- `git diff --check`: aprobado. No se ejecutó ninguna migración productiva ni envío real de correo.
- Capturas sintéticas fuera del repositorio: `%TEMP%/turnelia-consultorio05-evidence/consultorio-admin-desktop.png` y `consultorio-admin-mobile.png`.

La integración queda pendiente de revisión del PR y CI; no se realizó merge ni despliegue.
