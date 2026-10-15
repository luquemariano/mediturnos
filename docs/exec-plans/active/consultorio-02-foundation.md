# Entrega 02 — Fundación de Consultorio, salas y frontera de permisos

Estado: **PR #88 abierto — validación CI inicial verde; revisión pendiente**
Depende de: Entrega 01, mergeada en `main` como `c96c833`.
Alcance: fundación persistente y autorización del dominio Consultorio. No habilita miembros múltiples ni modifica producción.

## Objetivo

Incorporar el modelo mínimo de consultorio compartido para el piloto ALMA sin alterar cuentas profesionales existentes ni extender acceso clínico. La propietaria conserva su identidad y panel profesional; la administración del consultorio se autoriza por su rol administrativo en el consultorio, nunca por la cuenta propietaria de datos clínicos.

La entrega deja listo un consultorio, una o más salas y el registro de profesionales potenciales. No crea módulos recurrentes, invitaciones utilizables, agenda conjunta, turnos de consultorio ni suscripción comercial.

## Alcance funcional

1. `Consultorio`: cuenta organizacional administradora, nombre, zona IANA, duración predeterminada de módulo (240 minutos por defecto), horizonte de materialización configurable y estado.
2. `Sala`: pertenece a un consultorio, tiene nombre/código único dentro de él y estado. El piloto usará una sola sala, sin limitar el modelo a una.
3. `ConsultorioProfesional`: relación entre consultorio y un `Profesional` existente, con estado preparatorio/activo/suspendido/retirado y fechas de alta/baja. No cambia `Profesional.cuenta_id`, `ProfesionalPaciente`, disponibilidades, pacientes ni historia clínica.
4. Rol administrativo de consultorio: propietaria/administradora inicial. Sólo habilita el dominio administrativo propio; no equivale a administrador global.
5. Endpoints autenticados mínimos para que una administradora autorizada consulte y gestione la configuración propia del consultorio y sus salas en entorno de desarrollo. No exponer información clínica, pacientes, turnos ni agendas de profesionales.

## Reglas de seguridad obligatorias

- La identidad autenticada determina el consultorio autorizado; ningún `consultorio_id` enviado por cliente es autorización suficiente.
- Una administradora de consultorio no obtiene acceso a perfiles, evoluciones, documentos, estudios, pacientes ni turnos de otro profesional.
- Un profesional miembro no obtiene administración de salas ni de otros miembros.
- Un profesional puede seguir usando su cuenta, agenda, prestaciones y datos propios sin cambios de titularidad.
- No permitir que la API active membresías operativas, agregue profesionales reales ni envíe invitaciones en esta entrega.
- No crear datos de Valentina, ALMA ni pacientes reales; fixtures y seeds deben ser sintéticos.

## Persistencia y migración

- Crear una migración Alembic aditiva para las entidades y restricciones del dominio.
- `Consultorio.cuenta_id` debe referenciar una cuenta organizacional; validar tipo y unicidad en servicio.
- Proteger unicidad de sala por consultorio y de profesional por consultorio.
- Agregar FKs, índices y checks compatibles con PostgreSQL; validar migración desde base vacía en CI PostgreSQL.
- No tocar tablas clínicas incorporadas en Entrega 01 ni ejecutar migraciones fuera de entornos locales/CI.

## API y capas

Mantener `router → service → repository`.

- Las rutas administrativas resuelven la identidad actual y validan ownership administrativo en servicio.
- Responder 404 para recursos fuera del consultorio autorizado cuando evite enumeración; 403 sólo cuando corresponda a rol conocido sin permiso.
- Aplicar esquemas Pydantic explícitos; no devolver entidades ORM clínicas ni campos de cuentas no requeridos.
- No construir frontend de producción: sólo contratos API y pruebas. Si se agrega una vista técnica para E2E, debe quedar fuera de rutas públicas y sin datos reales.

## Pruebas requeridas

### Backend y PostgreSQL

- Crear consultorio y salas sintéticas; verificar unicidades y relaciones.
- Administradora A puede leer/modificar exclusivamente su consultorio y salas.
- Administradora A no puede consultar/alterar el consultorio B por ID.
- Profesional miembro no puede administrar consultorio, sala ni miembros.
- Administradora de consultorio no puede acceder a ninguna ruta clínica de un profesional miembro usando IDs conocidos.
- Crear relación `ConsultorioProfesional` no modifica `Profesional.cuenta_id`, vínculos `ProfesionalPaciente` ni visibilidad clínica.
- Pruebas de concurrencia/duplicación para alta de sala y relación profesional.
- Ejecución PostgreSQL real con migración desde esquema vacío y `git diff --check`.

### Regresión

- Mantener verde el conjunto clínico de Entrega 01.
- Ejecutar pytest focalizado y completo, Vitest, lint, build y Playwright según `docs/TESTING.md`.
- Toda falla de baseline se documenta y se clasifica; no se desactiva cobertura para ocultar una regresión.

## Fuera de alcance

- Módulos recurrentes, ocurrencias, exclusión de solapamientos de sala y vínculo de turnos.
- Invitaciones, aceptación, cupos activos y reservas provisionales.
- Agenda consolidada, ocupación y espacios libres.
- Cambios de disponibilidad profesional.
- Alta de actividades sin matrícula.
- Precios, Mercado Pago, suscripciones, facturación o cobros.
- Migración, despliegue, seed o cambios de datos en producción.

## Secuencia

### 02A — Preflight y contratos

1. **Completado:** lectura de `AGENTS.md`, workflow autónomo, plan y documentación canónica; rama `codex/consultorio-02-foundation` en `c96c833` (`main` y `origin/main`), sin cambios seguidos al inicio. Se preservó `docs/audits/` sin tocar.
2. **Completado:** línea base backend `878 passed, 28 skipped, 9 warnings`; Vitest `407 passed`; lint y build frontend correctos. Los skips backend corresponden a PostgreSQL no configurado; la advertencia principal preexistente es la deprecación `httpx`/Starlette.
3. **Completado:** API mínima para crear/consultar/actualizar consultorios y salas; autorización por identidad y asociación administrativa, sin usar IDs como permiso. El horizonte configurable queda en 90 días por la regla canónica: ventana pública de 60 días más 30 días de margen; no modifica esa ventana.

### 02B — Modelo y migración

1. **Completado:** modelos `Consultorio`, `Sala`, `ConsultorioAdministrador` y `ConsultorioProfesional`; repositorio y migración aditiva `y4z5a6b7c8d9`.
2. **Completado localmente:** modelos/restricciones en SQLite y cadena Alembic completa desde PostgreSQL vacío sintético. Unicidad de cuenta por consultorio, código de sala, vínculo profesional y propietaria única. El downgrade se bloquea si hay configuración persistida.

### 02C — Servicios y permisos

1. **Completado:** autorización `ConsultorioAdministrador` independiente de `CuentaUsuario`, roles globales y vínculos profesionales. Crear un consultorio exige cuenta organizacional propiedad del actor; la validación no transfiere `Profesional.cuenta_id` ni crea membresías.
2. **Completado:** pruebas HTTP negativas de consultorio/salas ajenas, miembro sin autoridad administrativa, y aislamiento clínico de perfil, evoluciones, documentos y estudios usando un paciente sintético compartido. No hay rutas de invitación/alta de integrantes ni de agendas ajenas.

### 02D — Gate de entrega

1. **Completado localmente:** pytest `883 passed, 30 skipped, 9 warnings`; PostgreSQL 17 con migración completa desde una base vacía y pruebas concurrentes de sala/vínculo `2 passed`; Vitest `407 passed`; lint y build correctos; Playwright `8 passed` con cleanup. La primera pasada completa de Vitest tuvo un fallo transitorio en paginación comercial; el test aislado (`11/11`) y la suite completa repetida (`407/407`) pasaron. Los 30 skips de pytest son módulos PostgreSQL sin URL en la ejecución SQLite; los dos nuevos módulos se ejecutaron por separado contra PostgreSQL real.
2. **Completado:** `git diff --check` limpio y revisión de seguridad del cambio. No se hallaron permisos clínicos derivados ni cambios de ownership. Un diagnóstico adicional `alembic check` reportó drift de metadatos preexistente en tablas ajenas a Consultorio; la cadena de migración y las cuatro tablas nuevas pasaron su validación PostgreSQL.
3. **Completado:** `ROADMAP.md`, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `SECURITY.md`, `TESTING.md`, `DECISIONS.md` y este plan actualizados. Sin landing ni ayuda pública: no hay UX de producción y la feature no está desplegada.
4. **Completado para el commit `5a9bd25`:** commit, push y PR #88 hacia `main`; run `38659022259` con Backend CI, PostgreSQL CI, Frontend CI y Playwright E2E CI en verde. La actualización documental genera una nueva revisión CI. No desplegar ni mergear.

## Criterio de cierre

La entrega se cierra únicamente cuando el dominio existe, sus restricciones pasan en PostgreSQL, las rutas administrativas no permiten enumerar ni gestionar consultorios ajenos, y el aislamiento clínico de Entrega 01 sigue probado. La capacidad multi-profesional continúa deshabilitada hasta las entregas de módulos e invitaciones.
