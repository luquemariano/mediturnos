# Entrega 03 — Módulos recurrentes y exclusión de sala

Estado: **IMPLEMENTADO EN RAMA — validación y PR en curso**
Depende de: Entrega 02, mergeada en `main` como `f667cc1`.
Alcance: motor de módulos semanales, ocurrencias materializadas y protección de la sala compartida. No habilita invitaciones ni cambios productivos.

## Objetivo

Permitir que la administradora de un consultorio configure módulos semanales para profesionales ya preparados en su consultorio. Cada módulo reserva una sala completa para un único profesional durante todo el intervalo, aunque no existan pacientes.

La recurrencia semanal es obligatoria. La duración predeterminada parte de la configuración del consultorio —240 minutos en el piloto— pero puede definirse en cada regla. El sistema materializa ocurrencias concretas dentro de un horizonte móvil de 90 días y evita solapamientos incluso ante operaciones concurrentes.

## Reglas de producto obligatorias

- Una sala no puede tener dos ocurrencias activas superpuestas; intervalos adyacentes `[inicio, fin)` son válidos.
- Una regla semanal no puede solaparse con ninguna regla vigente de la misma sala, aunque una de las ocurrencias todavía no haya sido materializada.
- Cada ocurrencia pertenece a una sala y a un profesional preparado/activo del mismo consultorio.
- Una ocurrencia puede derivar de una regla semanal, ser extraordinaria o ser una suspensión/excepción de una fecha concreta.
- Cambiar o suspender una ocurrencia/regla se rechaza si deja turnos activos fuera del módulo o asignados a otro profesional. Sólo se informa el conteo afectado; no se exponen pacientes, prestaciones, contactos ni datos clínicos.
- No cancelar ni reprogramar turnos automáticamente.
- La creación y reprogramación de turnos de profesionales vinculados a un consultorio debe verificar módulo vigente, coincidencia de profesional, límites `[inicio, fin)` y disponibilidad propia. Los flujos individuales sin vínculo de consultorio siguen sin cambio.
- Valentina puede consultar ocupación de sala y profesional asignado, pero nunca pacientes ni información clínica.

## Modelo y persistencia

Agregar mediante Alembic:

- `SerieModulo`: identidad estable de una asignación y continuidad de versiones.
- `ReglaRecurrenciaModulo`: sala, profesional, día de semana, hora civil, duración, zona IANA, vigencia desde/hasta, versión y estado.
- `OcurrenciaModulo`: intervalo concreto en UTC, sala, profesional, regla/serie opcionales, estado, origen recurrente/extraordinario/excepción y fecha civil de origen.
- `SolicitudCambioModulo` o estructura equivalente auditada para cambios bloqueados por turnos, sin payload clínico.

PostgreSQL debe usar `btree_gist` y una exclusión GiST por sala + `tstzrange(inicio, fin, '[)')`, limitada a estados que retengan el espacio. La migración debe validar extensión, compatibilidad y conflictos antes de habilitar la restricción.

La pareja regla/fecha civil debe ser idempotente. La generación usa `America/Argentina/Buenos_Aires` en el piloto y conserva la hora civil aun cuando la zona horaria tenga transiciones.

## API y permisos

Mantener `router → service → repository`.

- Sólo administradoras autorizadas pueden configurar reglas, módulos extraordinarios y suspensiones del consultorio propio.
- Los profesionales ven exclusivamente sus módulos y no pueden ampliar su alquiler.
- Las respuestas de ocupación incluyen sala, intervalo, estado y profesional asignado. No incluyen paciente, turno, prestación, documento ni dato clínico.
- No implementar invitaciones, aceptación de cupos, membresías administrables ni frontend de producción en esta entrega.
- No permitir cambios retroactivos de reglas: los cambios desde una fecha efectiva crean una nueva versión y preservan historial.

## Secuencia

### 03A — Contratos y generador de recurrencia

1. **Completado:** inspeccionados los servicios comunes de alta/reprogramación, reserva pública, agenda profesional y disponibilidad.
2. **Completado:** reglas semanales con hora civil IANA, resolución determinista de horas ambiguas (primer fold), omisión de horas inexistentes y pruebas de DST, vigencia, cruce nocturno y adyacencia.
3. **Completado:** contratos administrativos muestran sólo sala, intervalo, estado y profesional; no admiten pacientes, turnos ni datos clínicos.

### 03B — Migración y exclusión PostgreSQL

1. **Completado:** entidades `SerieModulo`, `ReglaRecurrenciaModulo`, `OcurrenciaModulo` y auditoría `SolicitudCambioModulo`; migración aditiva `z5a6b7c8d9e0` con FKs, checks, índices, `btree_gist`, validación de opclass/conflictos y exclusión GiST por sala/intervalo `[)`, sólo para ocurrencias activas.
2. **Completado:** PostgreSQL 17 real confirmó una sola creación en carrera solapada, rechazo SQLSTATE `23P01` en inserción conflictiva secuencial y aceptación de intervalos adyacentes; la exclusión queda como última defensa ante concurrencia.
3. **Completado:** cadena Alembic aplicada en base vacía; downgrade de esta entrega se rehúsa si hay serie/ocurrencia y el downgrade de Entrega 02 conserva su propia protección.

### 03C — Servicios, excepciones y protección de turnos

1. **Completado:** API administrativa para reglas semanales versionadas, módulos extraordinarios, cambios puntuales y suspensiones; autorización por `ConsultorioAdministrador` y vínculo profesional/sala del mismo consultorio.
2. **Completado:** expansión idempotente desde la fecha local hasta 90 días; GET administrativo y reserva/reprogramación extienden el horizonte transaccionalmente. Los generadores concurrentes serializan por fila de regla; `(regla_id, fecha_origen)` es la clave idempotente.
3. **Completado:** cambios de ocurrencia/regla con turnos activos devuelven HTTP 409 con sólo `turnos_afectados`, registran auditoría sin referencias clínicas y no alteran la ocurrencia/regla. No se modifican automáticamente turnos.
4. **Completado:** alta común, reserva pública y reprogramación validan ocurrencia activa, profesional, límites completos y disponibilidad propia. Profesionales no vinculados siguen el flujo previo.

### 03D — Gate

1. **Local aprobado:** pytest completo `893 passed, 33 skipped, 9 warnings`; Vitest `407 passed`; lint/build aprobados; Playwright `8 passed`; suite PostgreSQL CI `30 passed`; `git diff --check` limpio. Se registran avisos/deprecaciones preexistentes.
2. **Completado:** revisión de IDs ajenos, ownership administrativo, serialización de sala/regla/ocurrencia, exclusión GiST, conteos agregados y ausencia de consultas/devoluciones clínicas administrativas.
3. **En curso:** documentación, commit, push, PR y espera de CI.
4. **Respetado:** sin merge, despliegue, migración productiva, datos reales, emails ni cambios de agenda de miembros múltiples.

## Pruebas requeridas

- Dos administradoras compiten por módulos en la misma sala: sólo uno puede reservar el intervalo superpuesto.
- Módulos adyacentes no chocan.
- Reglas semanales que se cruzan se rechazan aunque las fechas se materialicen después.
- Generar dos veces no duplica ocurrencias.
- Profesional A no puede reservar dentro del módulo de B ni fuera de su módulo.
- Administradora ve ocupación sin pacientes ni metadatos clínicos.
- Suspender, modificar o reasignar con turnos activos queda bloqueado y comunica sólo cantidad.
- Profesionales sin relación consultorio mantienen el comportamiento individual actual.
- Integridad en PostgreSQL y ausencia de datos parciales ante conflicto/exclusión.

## Fuera de alcance

- Invitaciones, enlaces, aceptación de cuenta existente/nueva y cupos provisionales.
- Panel visual final del consultorio y calendario consolidado para uso comercial.
- Activación operativa de miembros múltiples.
- Actividades sin matrícula, precios, suscripciones, Mercado Pago, cobros o facturación.
- Despliegue, migración de producción, cambios de datos reales o envío de correos.

## Criterio de cierre

La entrega se cierra sólo si una sala queda protegida contra solapamientos, los módulos recurrentes y excepciones son transaccionales y auditables, los turnos de profesionales vinculados respetan sus franjas, y la propietaria no puede acceder a datos clínicos ajenos. La funcionalidad permanece sin desplegar. El cierre remoto depende de CI verde de la PR.
