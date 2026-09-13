# F12.1 — Discovery y diseño de lista de espera inteligente

Estado: **F12.2 base implementada; matching y ofertas pendientes**
Fecha de auditoría: 2026-09-12
Alcance: discovery y diseño. No se implementan modelos, endpoints, migraciones ni tests en esta fase.

## 1. Resumen ejecutivo

Se propone una lista de espera persistida por profesional y prestación, con preferencias civiles de fecha, hora y días de semana. La entrada tiene un ciclo de vida explícito (`activa`, `ofertada`, `convertida`, `cancelada`, `vencida`) y nunca crea un turno automáticamente. Un proceso de matching identifica un hueco liberado y genera una oferta de reserva con token aleatorio de un solo uso y vencimiento corto.

El MVP debe notificar a un solo candidato por vez, ordenado por compatibilidad y antigüedad. La reserva final debe llamar al flujo existente de creación de turnos; el token sólo autoriza la oferta y no reserva el horario. Si el hueco se ocupa, la oferta falla de forma segura y el candidato puede volver a participar mientras su entrada siga activa.

## 2. Auditoría del modelo actual

### Turno (`app/models/turno.py`)

- PK interna `id` entera; `identificador_publico` UUID textual único.
- FK a `pacientes`, `prestaciones` y `profesionales`; `paciente_id`, `prestacion_id` y `profesional_id` son obligatorias.
- `fecha_hora` y `fecha_fin` son `DateTime(timezone=True)`; constraint exige fin posterior al inicio.
- Estados observados: `reservado`, `confirmado`, `cancelado`, `finalizado`, `ausente`. No existe soft-delete.
- `autogestion_token_hash` es SHA-256, nullable y único; el token claro no se persiste.
- Índices por `profesional_id/fecha_hora` y `fecha_hora`; el solapamiento activo se protege adicionalmente en PostgreSQL por la constraint de exclusión `ex_turnos_profesional_intervalo_activo` (referenciada en `turno_service`).
- La duración se copia a `fecha_fin` desde `Prestacion.duracion_minutos`; por eso matching debe usar el intervalo completo, no sólo la hora inicial.

### Paciente (`app/models/paciente.py`)

PK entera; `usuario_id` nullable y único; nombre/apellido obligatorios; DNI único nullable; email y teléfono opcionales; `activo` booleano. El paciente público puede crearse durante booking y luego vincularse mediante `ProfesionalPaciente`. No hay timestamps ni soft-delete en este modelo.

### Profesional (`app/models/profesional.py`)

PK entera; FK obligatoria a `cuentas`; `activo`, `reserva_online_activa` y `slug_publico` único nullable. El slug es la identidad pública del profesional. No hay timestamps ni soft-delete.

### Prestación (`app/models/prestacion.py`)

PK entera; UUID público único `identificador_publico`; FK a profesional y especialidad; nombre, duración, precio, modalidad; flags `activa` y `habilitada_online`. No hay timestamps ni soft-delete: desactivar es cambiar `activa`.

### Disponibilidad y excepciones

`Disponibilidad` guarda franjas habituales por `profesional_id`, `dia_semana`, `hora_inicio`, `hora_fin`, `activa`. `DisponibilidadExcepcion` guarda fecha, tipo (`cierre_dia` o `franja_extraordinaria`), origen, franja opcional y `activa`, con índices por profesional/fecha/activa y unicidad parcial PostgreSQL/SQLite para cierres.

La función canónica es `validar_turno_dentro_disponibilidad`; la enumeración de huecos es `obtener_horarios_libres` en `app/services/disponibilidad_service.py`. Ambas operan con `America/Argentina/Buenos_Aires` y normalizan a UTC.

### Notificaciones y booking público

`Notification` es privada y requiere `user_id`; tiene tipo, título, mensaje, entidad (`entity_type/entity_id`), `read_at` y `created_at`, con índice de no leídas. No puede representar directamente a un paciente público sin usuario; el email debe ser un canal separado y, si luego el paciente tiene usuario, se puede crear una notificación privada.

El booking usa `slug_publico` y UUID público de prestación/turno. Exige profesional activo, reserva online activa, prestación activa y habilitada online, anticipación mínima de 2 horas y horizonte de 60 días. Los datos civiles se convierten con `a_utc`/`utc_a_zona_negocio`; no se deben comparar fechas locales como si fueran UTC.

## 3. Flujos que liberan o cambian horarios

| Caso | Mutación actual | Punto seguro para F12 |
|---|---|---|
| Profesional cancela | `routers/profesionales.py` → `cancelar_turno_profesional` → `aplicar_transicion_estado` → commit | Después del commit exitoso, publicar evento/outbox `turno_liberado` con snapshot previo del intervalo. |
| Paciente cancela autenticado | `turno_service.cancelar_turno_paciente` → commit | Mismo evento, sin duplicarlo desde el router. |
| Paciente cancela por autogestión | `public_booking_service.cancelar_reserva_por_token` → `cancelar_turno_profesional` → notificación pública | Unificar en el servicio de dominio; no enganchar sólo el endpoint público. |
| Profesional reprograma | router → `reprogramar_turno_profesional` → `reprogramar_turno` | Capturar el intervalo anterior antes de mutarlo; detectar el intervalo anterior después del commit. |
| Paciente reprograma por token | `public_booking_service.reprogramar_reserva_por_token` → `reprogramar_turno` | Igual que arriba; el cambio puede liberar sólo el intervalo anterior. |
| Eliminación física | No existe flujo de aplicación para eliminar turnos; sólo seed usa `db.delete` | No asumirlo como disparador del MVP; auditar cualquier futuro delete. |
| Disponibilidad | `disponibilidad_service` crea/actualiza/desactiva franjas y excepciones | No es una liberación de turno: puede crear o quitar huecos. En MVP sólo re-evaluar entradas en una tarea periódica o al reabrir una franja. |

`turno_service` bloquea la agenda con `pg_advisory_xact_lock(73421, profesional_id)` antes de validar/crear/reprogramar. La detección debe ejecutarse fuera de la transacción que cancela, mediante outbox o job idempotente, para no enviar email dentro de una transacción que aún podría revertirse.

## 4. Modelo propuesto

### `waitlist_entries`

Campos recomendados:

- `id` bigint PK interna.
- `identificador_publico` UUID textual único.
- `profesional_id`, `prestacion_id` y `paciente_id` nullable con FK. Para solicitudes públicas sin paciente existente, guardar `nombre_snapshot`, `email_snapshot` y `telefono_snapshot`; al vincular paciente, conservar snapshots para auditoría de contacto.
- `fecha_desde`, `fecha_hasta` inclusivas (`date`); `hora_desde`, `hora_hasta` opcionales (`time`); `dias_semana` como arreglo PostgreSQL no es portable a SQLite, por lo que para MVP conviene tabla hija `waitlist_entry_days(entry_id, dia_semana)` o JSON validado si ya existe soporte.
- `estado`, `origen`, `created_at`, `updated_at`, `notified_at`, `expires_at`.
- `version` o equivalente opcional para actualizaciones optimistas.

Separar una tabla `waitlist_offers` evita sobrecargar la entrada: `id`, `entry_id`, `turno_id` nullable, intervalo ofrecido, `token_hash`, `expires_at`, `sent_at`, `claimed_at`, `status`, `created_at`. El token claro sólo aparece en el email/enlace y nunca en base de datos ni logs.

Estados recomendados de la entrada: `activa` → `ofertada` → `convertida`, con salidas desde `activa` a `cancelada`/`vencida` y desde `ofertada` a `activa` cuando expira o se ocupa el hueco. `ofertada` no significa turno reservado. Una oferta tiene estados propios `pendiente`, `aceptada`, `expirada`, `rechazada` o `fallida`.

## 5. Reglas de negocio

- Una persona puede tener varias entradas si cambia profesional, prestación o preferencias. Rechazar sólo duplicados exactos activos: mismo profesional, prestación, paciente/contacto normalizado y mismos criterios de fecha/hora/días.
- Exigir prestación activa y perteneciente al profesional; para origen público exigir además `reserva_online_activa` y `habilitada_online`. Exigir profesional activo.
- `fecha_desde` no puede ser pasada; `fecha_hasta >= fecha_desde`; por defecto aplicar el horizonte actual de 60 días y una ventana máxima configurable (recomendación MVP: 60 días).
- La anticipación mínima de 2 horas se aplica al ofrecer y al reservar, no sólo al crear la entrada.
- Hora omitida significa cualquier hora. Si sólo se informa una hora, rechazar: usar intervalo completo o presets de UI. `hora_desde <= hora_hasta`; días son opcionales y usan el mismo `weekday()` que disponibilidad.
- Al desactivar prestación o profesional, no borrar entradas: pasar a `vencida`/`cancelada` con motivo interno y no notificar. Si se reactiva, la decisión de reactivar entradas queda pendiente; MVP no las reactiva automáticamente.
- No incluir observaciones clínicas ni información de turnos previos en la lista o email.

## 6. Matching

El candidato debe cumplir: mismo profesional y prestación; entrada activa; fecha civil dentro del rango; día permitido; hora inicial dentro de preferencia; intervalo completo dentro de disponibilidad efectiva y excepciones; sin solapamiento con turnos activos; anticipación y horizonte vigentes.

No duplicar disponibilidad. Reutilizar `obtener_horarios_libres(db, prestacion_id, fecha, ...)` para consultar candidatos concretos, y `validar_turno_dentro_disponibilidad` como defensa final. Para una cancelación, partir del intervalo liberado (`fecha_hora`, `fecha_fin`) y comprobar si una de las horas discretas que genera la función coincide con el inicio liberado. Si en el futuro se permiten horarios arbitrarios, extraer una función común de intervalos, no crear una segunda implementación.

El matching debe ser idempotente: clave lógica por `turno_id + entry_id + intervalo`; reintentos no deben producir ofertas duplicadas. Orden MVP: compatibilidad exacta de hora, luego mayor solapamiento con preferencia, luego `created_at` ascendente.

## 7. Concurrencia y reserva

Opciones: (A) un paciente por vez reduce spam y hace simple el estado; (B) varios maximiza conversión pero produce más enlaces inválidos; (C) exclusividad temporal necesita mantener un hold y complica la protección actual. Se recomienda **A para MVP**: crear una oferta para el primer candidato y marcar la entrada `ofertada` dentro de una transacción corta.

Al aceptar, verificar hash, expiración, estado de oferta, estado de entrada y disponibilidad actual; luego llamar a `crear_turno` dentro de la misma transacción/lock de agenda. El advisory lock y la constraint de exclusión siguen siendo la autoridad. Un `409 horario no disponible` marca la oferta como fallida y permite avanzar al siguiente candidato. Abrir el email no bloquea el turno. No hacer `db.commit()` en la detección hasta que el estado de oferta esté persistido.

## 8. UX

### Profesional

Agregar “Lista de espera” como sección lateral. MVP: tabla paginada con paciente/contacto, prestación, rango, preferencia, antigüedad y estado; filtros por estado/prestación/fecha. Acciones: ver detalle, cancelar/desactivar y eliminar sólo si existe una razón operativa clara; “convertir manualmente” debe abrir el flujo actual de crear turno con datos precargados, no saltarse validaciones. Mostrar una alerta mínima cuando haya ofertas pendientes o huecos en proceso.

### Pública (`/reservar/:slug`)

Tras una búsqueda sin horarios convenientes, CTA “¿No encontraste un horario? Sumate a la lista de espera”. Mantener prestación y profesional ya seleccionados; pedir rango civil, preferencia opcional y nombre/email/teléfono. Reutilizar el subformulario de paciente de booking, pero no crear automáticamente un turno. Confirmar mediante mensaje genérico y email de verificación/oferta; aplicar rate limit y no revelar si un email ya tiene una entrada.

## 9. Notificaciones

Profesional autenticado: notificación privada al crearse una entrada vinculada a un paciente con usuario; email opcional “hay una solicitud en lista de espera” sin datos clínicos. Al detectarse una oferta, la UI puede mostrar estado, pero el paciente recibe email transaccional con prestación, profesional, fecha/hora, zona horaria, expiración y enlace seguro.

Al aceptar, enviar confirmación de turno por el flujo existente. Notificar al profesional que el paciente tomó el turno. Usar outbox/cola para email, reintentos e idempotencia; no depender de `Notification` para destinatarios públicos.

## 10. Seguridad

Público: sólo slug, prestación habilitada, preferencias del propio formulario y datos mínimos. Nunca exponer IDs internos, existencia de otras entradas, pacientes ni disponibilidad privada. En respuestas públicas usar UUID/slug y mensajes indistinguibles para duplicado/no existencia cuando corresponda.

Generar token con `secrets.token_urlsafe(32)`, almacenar sólo SHA-256, limitar longitud, scopearlo a `waitlist_offer`, usar expiración corta (recomendación: 24 h), un solo uso y comparación por hash. No reutilizar el token de autogestión del turno aunque el patrón de `hash_token_autogestion` sea una referencia útil. Rate limit para alta pública y aceptación; registrar sólo IDs internos, tipo de evento y resultado, nunca token, email completo o datos clínicos. Considerar hash/HMAC de email para deduplicación si no se puede vincular paciente.

## 11. Migración Alembic propuesta (no crear ahora)

Crear `waitlist_entries` y `waitlist_offers`; si se elige normalizar días, crear `waitlist_entry_days`. FKs a profesionales/prestaciones/pacientes con `RESTRICT` o `SET NULL` según política de retención; no usar cascada que borre historial sin decisión. Constraints para estado/origen, rango de fechas, horas y expiración. Índices: `(profesional_id, prestacion_id, estado, fecha_desde, fecha_hasta)`, `(estado, expires_at)`, `token_hash` único, y `turno_id`/intervalo para idempotencia. Unicidad de duplicados activos requiere índice parcial PostgreSQL; si se necesita SQLite en tests, reforzar también en service y testear la diferencia.

Usar `DateTime(timezone=True)` para instantes, `date/time` para preferencias civiles, `gen_random_uuid()` sólo si ya es una dependencia aceptada; actualmente el código genera UUID en aplicación. Verificar `CHECK` y tipos contra PostgreSQL y SQLite antes de migrar. La oferta no debe usar una exclusion constraint propia: el turno existente es la autoridad.

## 12. Test plan mínimo para implementación

Alta autenticada y pública válida; normalización y duplicado exacto; profesional/prestación inactivos o no pertenecientes; rangos pasados, >60 días y horas inválidas; matching por profesional, prestación, duración, fecha, día y hora; no matching por excepción, disponibilidad o turno ocupado; cancelación profesional, paciente autenticado y pública libera hueco; reprogramación libera sólo intervalo anterior; oferta expirada/cancelada no participa; dos aceptaciones concurrentes del mismo hueco; token inválido, scope incorrecto, reutilizado y expirado; no enumeración/rate limit; serialización correcta en `America/Argentina/Buenos_Aires`, DST y formato 24 h; PostgreSQL real para advisory lock/exclusion constraint.

## 13. Decisiones de producto

| Decisión | Opciones | Recomendación | Motivo |
|---|---|---|---|
| Estados | 4 estados simples / entrada + oferta separadas | Entrada `activa/ofertada/convertida/cancelada/vencida` + oferta propia | Evita confundir aviso con reserva y permite reintentos. |
| Notificación | Email directo / outbox-worker | Outbox-worker idempotente | No acopla email a commit y permite reintentos. |
| Personas notificadas | Una / varias / hold exclusivo | Una por vez | Menor complejidad y menos enlaces inválidos en MVP. |
| Expiración | Sin vencimiento / 24 h / configurable | 24 h para oferta; entrada hasta `fecha_hasta` | Reduce obsolescencia sin borrar demanda. |
| Preferencias | Cualquier hora / rango / slots | Rango opcional + días opcionales | Expresivo y simple de validar. |
| Creación pública | Siempre / sólo reserva online / autenticada | Sólo reserva online activa, con email | Respeta el control existente y permite demanda anónima segura. |
| Navegación profesional | Nueva ruta dedicada / panel integrado | Sección lateral integrada | Menor carga cognitiva y reutiliza agenda/turnos. |

## 14. Riesgos y decisiones pendientes

Riesgos principales: duplicar o enganchar mal la detección en múltiples cancelaciones; diferencias SQLite/PostgreSQL en constraints; cambios de duración/prestación después de crear la entrada; volumen de escaneo; emails que llegan después de ocupar el hueco; y retención de datos de contacto públicos.

Pendiente decidir: duración exacta de una oferta; si una entrada ofertada vuelve automáticamente a activa; si el paciente debe confirmar email antes de crearla; política de reactivación al volver una prestación; granularidad de slots frente a horarios arbitrarios; proveedor/worker de outbox; retención y borrado de snapshots; y si “convertir manualmente” requiere auditoría adicional.

## 15. Archivos que se tocarían al implementar

Backend: `app/models/waitlist_entry.py`, `app/models/waitlist_offer.py`, `app/models/__init__.py`, schemas, repositorios y servicios de waitlist; extensión controlada de `turno_service.py`/`public_booking_service.py` mediante evento común; worker/outbox y email; routers de profesional y booking público; registro en `app/main.py`; Alembic. Frontend: servicios API, pantalla/sección lateral profesional y formulario/estado en la ruta pública de reserva. Tests unitarios, HTTP y PostgreSQL.

## 16. Estimación de subfases

1. Contratos y migración: 0,5–1 día.
2. Dominio, matching y oferta idempotente: 1,5–2 días.
3. Integración segura con cancelación/reprogramación y worker: 1–1,5 días.
4. UX profesional y pública: 1,5–2 días.
5. Tests SQLite/PostgreSQL, seguridad y observabilidad: 1–1,5 días.

Estimación total: 5,5–8 días de desarrollo, sujeta a las decisiones pendientes y a la infraestructura real de email/worker, actualmente **NO DETERMINADA**.

## Implementación F12.2

La base quedó implementada: modelo `WaitlistEntry`, estados y constraints, migración Alembic, repository, service y API privada autenticada. La API expone creación/listado/cancelación profesional en `/waitlist`; deriva el profesional desde el usuario autenticado y no acepta `profesional_id` del cliente. La creación pública, matching, ofertas, ventana exclusiva, emails, scheduler y UI quedan pendientes de F12.3 o posteriores.

## Implementación F12.3

F12.3 incorpora `ReleasedSlot` y `find_matching_waitlist_entries`. El matching filtra candidatos activos por profesional, prestación y fecha; luego valida preferencias en horario local y confirma el inicio mediante `obtener_horarios_libres`, reutilizando disponibilidad, excepciones y turnos ocupados. Se dispara después de commits exitosos de cancelación y reprogramación, evaluando únicamente el intervalo anterior en este último caso. No cambia estados, persiste matches ni crea ofertas, tokens, emails o scheduler.

**F12.3 MATCHING: LISTO PARA REVALIDACIÓN**
