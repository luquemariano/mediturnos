# Entrega 08A — Preflight de comunicaciones controladas en staging

Estado: **IMPLEMENTADA LOCALMENTE; PR/CI PENDIENTES**. Rama: `codex/staging-comms-preflight`. Base verificada: `origin/main` en `f797b19447fa93069a4aa5f1c25cd3abf3d9ba1e`.

## Objetivo y límites

Preparar validación local para una futura prueba manual controlada de correo transaccional y recordatorios WhatsApp con acciones firmadas de confirmar/cancelar. Este cambio no envía correo/WhatsApp, no usa datos reales, no accede a staging remoto/producción, no cambia DNS, Caddy, secretos, pagos ni cuentas de Valentina y no toca `docs/audits/`. No necesita migración.

## Auditoría actual

- `Settings` fuerza `EMAIL_PROVIDER=in_memory` y `WHATSAPP_PROVIDER=fake` en staging mientras las banderas de envío están apagadas. Resend ya requiere allowlist y la comprueba en `ResendEmailProvider` antes de `requests.post`.
- WhatsApp Cloud API usa `MetaWhatsAppProvider`; el worker sólo envía recordatorio con opt-in y conserva idempotencia por turno/fecha. No había allowlist de teléfonos destinatarios en el envío.
- El worker compartía variables de provider, pero su enum de `APP_ENV` no incluía `staging` ni aplicaba los guards staging, por lo que el comando de recordatorios no era compatible con este entorno.
- Meta utiliza mapping local `appointment_reminder_v2` (`es_AR`) con botones URL y tokens firmados de confirmar/cancelar. Los endpoints GET presentan una confirmación; POST valida y aplica la acción. El webhook valida firma/verify token y registra mensajes/estados, pero no ejecuta acciones inbound ni permite comprobar la aprobación externa del template.
- No se ha efectuado comprobación externa de credenciales, Meta Business Manager, plantilla o webhook. Queda **NO DETERMINADO** hasta una futura prueba manual autorizada.

## Diseño y cambios de esta entrega

1. Mantener defaults fake/in-memory y exigir `APP_ENV=staging` para ejecutar el preflight. El CLI lee un env file privado y sólo emite nombres de variable y estados; no inicializa la aplicación, providers, DB ni conexiones.
2. Validar variables requeridas, allowlists válidas, HTTPS y callback Meta dedicado, IDs de teléfono/cuenta test allowlisted y mapping local del template.
3. Añadir `STAGING_WHATSAPP_RECIPIENT_ALLOWLIST` externa. La normalización se realiza con el mismo helper de teléfono que usa el recordatorio. Meta rechaza antes de enviar cuando el destinatario no está allowlisted. Resend conserva su guard existente.
4. Extender configuración del worker para staging y hacer que `APP_ENV=production` rechace banderas/allowlists exclusivas de staging.
5. No modificar la semántica de reintentos/idempotencia, endpoint webhook ni template payload.

## Procedimiento posterior, sólo con autorización separada

Mariano deberá aportar por canal privado: correos receptores bajo su control y aprobación de su uso; teléfono de prueba controlado con opt-in y aprobación para recibir mensajes; confirmar en Meta Business Manager que app/número son de prueba; `phone_number_id`, `business_account_id`, versión Graph, token de acceso de prueba, verify token y app secret dedicados; remitente/key Resend dedicados si se prueba email; y ventana/horario de ejecución. No compartir secretos en PR, documentación o chat.

Orden de operación posterior: (1) preparar archivo privado externo con permisos restrictivos y defaults fake; (2) agregar sólo los receptores aprobados y credenciales/IDs de prueba; (3) correr preflight y revisar estado sin copiar valores; (4) registrar callback HTTPS en Meta, verificar challenge/firma y comprobar aprobación del template en idioma/categoría correctos; (5) comprobar con provider fake los escenarios e idempotencia; (6) activar un canal a la vez, iniciar con un solo receptor/turno sintético propio y obtener autorización expresa antes del envío; (7) verificar una evidencia sanitizada de aceptación/estado, sin compartir teléfono, correo, tokens, IDs secretos ni contenido; (8) desactivar feature flags, volver a `in_memory`/`fake`, quitar credenciales de prueba del runtime y confirmar provider seguro. La falta de webhook/plantilla aprobada o discrepancia de allowlist bloquea el envío.

Rollback: apagar inmediatamente `STAGING_EMAIL_SEND_ENABLED`, `STAGING_WHATSAPP_META_ENABLED` y `WHATSAPP_ENABLED`; fijar proveedores in_memory/fake; retirar allowlists y credenciales del archivo privado según el procedimiento del operador; reiniciar sólo el stack staging cuando esa operación futura se autorice; revisar únicamente estados sanitizados. Esta entrega actual no ejecuta ese procedimiento.

## Pruebas y aceptación

- Unitarias/preflight: defaults, ambiente no staging, required env presence, allowlist válida/vacía/malformada, callback no HTTPS o host productivo, flags desalineadas, template mapping y no exposición de valores.
- Integración fake/in-memory: recordatorio generado; enlaces firmados de confirmación/cancelación; `POST` de acción con snapshot validado e idempotencia; retry de recordatorio no duplica envíos; allowlist permite sólo destinatarios declarados; provider no se invoca ante rechazo.
- Seguridad config: Settings y worker rechazan config exclusivamente staging cuando `APP_ENV=production`.
- PostgreSQL: no hay cambios de schema; ejecutar suite PostgreSQL acordada como regresión, especialmente recordatorios/acciones.
- Calidad: tests focalizados, `verify.ps1 -Full`, `verify.ps1 -E2E`, PostgreSQL, lint/build y `git diff --check`.
- No se permite ningún request real de red a Resend/Meta. Providers de pruebas son fake/in-memory y los tests de provider HTTP usan transportes simulados.

## Estado de ejecución

- [x] Confirmar `origin/main` actualizado y crear rama; `docs/audits/` se preserva sin tocar.
- [x] Auditar configuración, worker, Resend, WhatsApp, webhooks y rutas de acción.
- [x] Implementar preflight sin red, allowlist de WhatsApp en servicio/provider/smoke y guards de Resend directos, worker y production.
- [x] Agregar pruebas fake/in-memory de recordatorio, idempotencia, confirmación/cancelación HTTP, allowlists, preflight y configuración de worker; actualizar documentación y env examples.
- [x] Validar localmente: pruebas focales 73 passed; `verify.ps1 -Full` completado; PostgreSQL 17 efímero con Alembic desde cero y suites CI 39 passed; `verify.ps1 -E2E` 17 passed; preflight sobre `.env.staging.example` aprobado en modo seguro; `git diff --check` limpio. No se ejecutó ninguna migración fuera de las bases de prueba y no hubo llamadas a proveedores reales.
- [ ] Revisión final, commit/push/PR a `main` y CI verde. No mergear ni desplegar.

## Intervención propietaria pendiente para prueba futura

No bloquea la implementación/PR de esta entrega. Sí bloquea una prueba real posterior: correos/teléfono receptores bajo control de Mariano, consentimiento, IDs y credenciales de prueba Meta, confirmación de plantilla/webhook y autorización separada para un envío real controlado.
