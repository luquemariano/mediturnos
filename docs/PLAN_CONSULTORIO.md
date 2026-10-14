# Plan Consultorio — diseño técnico y planificación

Estado: **DISEÑO FUNCIONAL APROBADO — implementación pendiente**
Fecha: **2026-10-14**
Alcance: piloto de Valentina y diseño extensible a varios consultorios, salas y profesionales. Este documento describe el estado objetivo; no implica que la funcionalidad esté implementada ni autoriza cambios de código, migraciones, cobros o despliegues.

## Objetivo y reglas aprobadas

El Plan Consultorio reúne en una suscripción el uso administrativo de un espacio físico compartido. En el piloto existe un consultorio y una sala, cuatro profesionales y módulos de alquiler de cuatro horas. La duración predeterminada del módulo es configurable para nuevas asignaciones. El diseño admite varias salas y consultorios.

Cada módulo activo reserva la sala completa para un solo profesional, con independencia de que tenga pacientes. La asignación semanal recurrente es parte del MVP: Valentina configura varios días por semana y uno o más módulos en cada día. El profesional administra sus pacientes, prestaciones y turnos dentro de sus módulos y de su disponibilidad propia. La API rechaza turnos sin una ocurrencia vigente, turnos fuera de sus límites o disponibilidad propia, módulos superpuestos para una sala y turnos que no correspondan al profesional asignado.

Cada profesional conserva su cuenta y panel actuales. Valentina usa la misma identidad para cambiar entre su panel profesional y un panel administrativo separado. Ser propietaria del consultorio permite administrar membresías e instalaciones y consultar la ocupación del espacio; no confiere acceso clínico ni permiso para editar agendas ajenas.

El flujo de incorporación es: Valentina configura el profesional y su recurrencia de módulos; después emite invitación por correo o enlace. El invitado acepta con una cuenta existente o crea su cuenta profesional individual y encuentra precargados los días y horarios autorizados. Puede gestionar su disponibilidad dentro de esos bloques; nunca puede ampliar la autorización de alquiler. Las historias clínicas, evoluciones, solicitudes/revisiones de estudios y documentos pertenecen al profesional que las genera o recibe. Vincular al mismo paciente con otro profesional no comparte automáticamente información clínica. Los prestadores sin matrícula se habilitan según la actividad elegida, sin datos ficticios.

Una cuenta del consultorio administra una suscripción. Esta fase no modifica precios públicos, planes comerciales, cobros ni suscripciones existentes. La migración desde una cuenta individual debe preservar identidad, perfil y datos, y evitar cobros duplicados; la regla de transición requiere decisión comercial antes de activarse.

## Inspección del estado real

La propuesta se contrastó con el checkout local en `main`. En la inspección inicial, Git reportó `main...origin/main` sin diferencias seguidas y `docs/audits/` como no seguido. El directorio de auditoría se conservó intacto.

Hallazgos relevantes del código y la documentación:

- `Cuenta` admite `individual` y `organizacion`, `CuentaUsuario` ya representa membresías y `Suscripcion.cuenta_id` es único. El alta actual crea una cuenta individual y una suscripción profesional con trial.
- `Profesional.cuenta_id` es obligatorio y vincula cada perfil profesional con una cuenta. Una relación profesional–consultorio separada permite mantener la cuenta individual sin mover ni duplicar el perfil.
- `ProfesionalPaciente` ya relaciona pacientes con profesionales. `Turno` y `Disponibilidad` están particionados por profesional. El turno conserva su fin calculado al crearse.
- PostgreSQL ya protege turnos activos superpuestos para el mismo profesional con una exclusión GiST `[)` y el flujo serializa reservas por profesional. La exclusión no cubre una sala compartida entre profesionales.
- `EvolucionClinica` guarda `profesional_id`, pero su lectura profesional consulta todas las evoluciones por paciente. `ClinicalProfile` tiene una fila por paciente. `PatientDocument` se lista por paciente tras comprobar el vínculo profesional–paciente. Hace falta cambiar consulta y modelo de ownership; los permisos de cuenta por sí solos no bastan.
- `StudyRequest` y `StudyReview` guardan profesional; las cargas de paciente asociadas a solicitud deben heredar ese alcance y no convertirse en documentos visibles para todo el consultorio.
- El catálogo actual de prestaciones exige especialidad. El alta exige matrícula. Hace falta modelar actividad y validar los requisitos de matrícula de esa actividad.
- La auditoría del 14/10/2026 registra como pendientes el equipo/invitaciones/cupos, sala y agenda consolidada; documenta además riesgos clínicos, WhatsApp/webhook, backups y validaciones fallidas.

Referencias inspeccionadas: `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/PRODUCT.md`, `docs/CURRENT_STATE.md`, `docs/DECISIONS.md`, `docs/WORKFLOW.md`, `docs/TESTING.md`, `docs/DEPLOYMENT.md`, `docs/SECURITY.md`, `docs/ROADMAP.md`, `docs/audits/AUDITORIA_VALENTINA_2026-10.md`; modelos y servicios de cuentas, profesionales, pacientes, turnos, disponibilidad, evoluciones, documentos, estudios y suscripciones; pruebas de turnos concurrentes, permisos clínicos, cuentas y suscripciones.

## Arquitectura propuesta

Mantener el flujo actual `router → service → repository` y añadir un dominio de consultorio. Las rutas del panel consultorio usan autenticación normal y validan membresía/rol en cada request; la lógica de negocio vuelve a comprobar ownership y estado. El frontend añade un contexto/panel administrativo separado del panel profesional, sin convertir a la propietaria en administradora global ni reutilizar endpoints clínicos para obtener una vista de equipo.

La entidad de cuenta sigue siendo el sujeto de la suscripción. Un `Consultorio` se asocia a una cuenta organizacional que la administra y agrega salas y membresías. Una tabla de membresía del consultorio vincula perfiles profesionales existentes con el consultorio; no cambia `Profesional.cuenta_id`. Así, durante una transición, Valentina y los invitados conservan usuario, perfil profesional, agenda individual, cuenta e historial propios. La cuenta organizacional no pasa a ser propietaria clínica de sus datos.

La relación entre `CuentaUsuario` y las personas profesionales se mantiene separada: `CuentaUsuario.rol_cuenta` sirve a la gestión de la cuenta/suscripción; `ConsultorioProfesional` concede la pertenencia operativa al equipo; `Profesional` sigue siendo el límite clínico. Las autorizaciones nunca se deducen sólo de `cuenta_id` o de ser propietario.

### Modelos objetivo

Los nombres son conceptuales; se deben adaptar a las convenciones y relaciones existentes al implementar.

| Entidad | Datos/reglas propuestos |
|---|---|
| `Consultorio` | `id`, `cuenta_id` organizacional único, nombre, zona horaria IANA (piloto `America/Argentina/Buenos_Aires`), duración de módulo predeterminada en minutos, horizonte de materialización y estado/auditoría. |
| `Sala` | `id`, `consultorio_id`, nombre/código, estado; unicidad del nombre/código dentro del consultorio. La misma estructura admite varias salas. |
| `ConsultorioProfesional` | consultorio, `profesional_id`, estado (`activo`/`suspendido`/`retirado`), fecha de alta/baja; unicidad de profesional por consultorio. No reemplaza `ProfesionalPaciente`. |
| `InvitacionConsultorio` | consultorio, profesional preconfigurado, email normalizado, token aleatorio de un solo uso almacenado como hash, invitante, vencimiento (7 días iniciales, configurable), reserva provisional de plaza, revocación/consumo y timestamps. No guardar el token plano ni incluirlo en logs. |
| `SerieModulo` | agrupa la programación de una persona en una sala/consultorio y da continuidad a sus versiones; una reasignación futura cierra la vigencia anterior y crea la nueva versión/serie. |
| `ReglaRecurrenciaModulo` | serie, sala, profesional asignado, día de semana, hora local, duración, zona IANA, vigencia desde/hasta, versión y estado. Cada fila representa un módulo semanal; varios días o módulos por día se representan con varias reglas. La vigencia se versiona, no se reescribe retroactivamente. |
| `OcurrenciaModulo` | reserva concreta materializada desde una regla o creada como extraordinaria; regla/serie nullable, sala, profesional, inicio/fin como instantes, fecha/hora local de origen, estado y marca de excepción/suspensión. El intervalo es semiabierto `[inicio, fin)`. Una ocurrencia es la unidad de exclusión, turnos y cambios particulares; la pareja regla/fecha local es idempotente. |
| `SolicitudCambioModulo` | serie/ocurrencias afectadas, tipo y valores propuestos, estado, solicitante/resolutor/confirmador y timestamps. La respuesta para Valentina sólo incluye cantidad de turnos activos afectados; el profesional ve sus propios turnos para resolverlos. |
| Historial de regla/ocurrencia | registrar cambio, suspensión, agregado extraordinario, asignación, actor, motivo y transición de estado. Evitar sobrescribir la historia operativa. |
| Actividad profesional | catálogo/identificador de actividad con política de matrícula y prestaciones compatibles. Ningún valor ficticio para satisfacer una restricción clínica. |

Para el piloto se configura una sala y duración predeterminada de 240 minutos. Las siguientes salas y duraciones son configuración; no requieren otro diseño de tablas. La duración configurada se aplica a nuevas reglas/módulos. Cambiar la configuración no acorta ni extiende reglas vigentes u ocurrencias ya reservadas.

### Recurrencia semanal y horizonte de generación

Las reglas semanales y las ocurrencias concretas son parte del MVP. La regla conserva el patrón y su vigencia; las ocurrencias son filas concretas protegidas por PostgreSQL y sirven para disponibilidad, asignación de sala y vínculo de los turnos. No se permiten reglas sin límite práctico que queden validadas sólo contra las ocurrencias ya materializadas: al crear/modificar una regla se serializa la operación por sala y se verifica el patrón semanal contra todas las reglas vigentes, además de insertar/generar ocurrencias dentro del horizonte en la misma transacción.

**Horizonte recomendado:** generar 90 días móviles desde el presente: los 60 días del booking público actual más 30 días de margen. La API pública limita la disponibilidad a fechas civiles dentro de 60 días y la reserva/reprogramación a `ahora + 60 días`; el endpoint autenticado de turnos no muestra un límite superior equivalente. El horizonte de 90 días es de materialización y no amplía el booking público. Debe ser configurable y nunca menor al mayor horizonte de reserva habilitado. Un proceso idempotente diario extiende la ventana; al consultar o reservar una fecha futura, el backend verifica cobertura y materializa las ocurrencias necesarias antes de responder/confirmar. Si el producto decide permitir reservas autenticadas más allá de los 90 días, esa ventana debe aumentar junto con el horizonte o generar ocurrencias bajo demanda hasta la fecha pedida.

La generación conserva la hora civil en la zona del consultorio y convierte cada ocurrencia a instantes inequívocos; cubre transiciones DST, persistencia y reconstrucción idempotente. La inserción por lote de ocurrencias usa la misma transacción y bloqueo por sala/regla que la modificación de recurrencia. Un fallo de exclusión aborta el cambio completo, sin dejar regla activa parcialmente materializada.

### Exclusión, agenda y turnos

1. PostgreSQL debe rechazar intervalos superpuestos en la misma sala entre ocurrencias que retienen el espacio. Usar exclusión GiST sobre `sala_id` y `tstzrange(inicio, fin, '[)')`, con `btree_gist`, excluyendo estados suspendidos/cancelados que liberan la sala. Intervalos adyacentes son válidos. La migración comprueba extensión y conflictos antes de activar la restricción.
2. Al agregar una regla, bloquear la sala (o usar advisory transaction lock estable), validar patrón semanal completo y generar ocurrencias del horizonte en la misma transacción. La restricción de exclusión resuelve concurrencia y protege también módulos extraordinarios y cambios puntuales.
3. Agregar al turno de consultorio referencia a `OcurrenciaModulo` y garantizar que el profesional coincide con el asignado. Los turnos históricos mantienen la referencia nula y siguen el flujo individual existente.
4. En creación/reprogramación de turno, bloquear ocurrencia y comprobar estado, profesional, límites `[inicio, fin)` y disponibilidad propia del profesional. Todos los canales de alta deben usar la regla común (panel, booking público, acciones por enlace, pago u otros flujos aplicables).
5. Mantener la exclusión actual de turnos por profesional. La ocupación de sala se asegura reservando la ocurrencia completa, no asignando turnos a una sala de forma independiente.
6. El bloqueo serializa altas/reprogramaciones frente a suspensión, cambio de asignación o intervalo. Las reglas de fecha requieren validación transaccional del servicio y pruebas PostgreSQL; un check SQL por sí solo no alcanza para reglas entre filas.

### Cancelación, reprogramación y cambio de asignación

- Una ocurrencia recurrente puede modificarse para una fecha concreta sin cambiar la regla. El patrón recurrente puede versionarse desde una fecha efectiva; las ocurrencias pasadas y las futuras comprometidas se preservan. Se admiten módulos extraordinarios y suspensiones de fechas concretas.
- Si un cambio propuesto intersecta turnos activos, no se aplica y a Valentina se le muestra únicamente el conteo afectado. Puede crear una solicitud para el profesional asignado. El profesional resuelve sus turnos desde su propia agenda; no se envían nombres, prestaciones, contactos ni estados a Valentina.
- Tras resolverlos, el profesional marca la solicitud como lista y Valentina confirma el cambio. La confirmación recalcula el impacto y valida ausencia de turnos afectados, asignación vigente y disponibilidad de sala. La aprobación del profesional nunca omite restricciones ni fuerza el cambio.
- Nunca se cancelan ni reprograman pacientes automáticamente. Si un cambio no afecta turnos comprometidos y no genera conflicto, Valentina puede confirmarlo directamente.
- Cambiar sala, profesional, inicio, fin o duración de una ocurrencia/regla se rechaza si algún turno activo quedaría fuera de límites o correspondería a otro profesional. El cambio no altera turnos históricos; el traslado de un turno sigue el flujo explícito del profesional y valida destino y ownership.
- Reprogramar un turno sigue el flujo existente y valida el módulo destino dentro de la misma transacción. Un cambio de módulo no modifica turnos históricos por efecto lateral.
- Si se retira a un profesional, se impiden nuevos módulos/turnos y se resuelven sus módulos/turnos futuros mediante cancelación o traslado auditado. No se borran historias clínicas.
- Las reglas de tarifa, devolución o compensación por cancelación de alquiler quedan fuera del alcance técnico aprobado y requieren definición comercial/contractual.

## Profesionales, invitaciones y permisos

### Roles efectivos

| Acción | Propietaria del consultorio | Profesional miembro | Administrador global |
|---|---:|---:|---:|
| Gestionar salas, módulos e invitaciones del consultorio | Sí | No, salvo permiso administrativo futuro explícito | Según las herramientas globales existentes, fuera del panel de consultorio |
| Ver ocupación de salas y profesional asignado | Sí, sólo datos de módulo | Sólo sus propios módulos | No se amplía en este plan |
| Ver/modificar turnos de pacientes de otro profesional | No | No | Sólo acceso administrativo global existente, auditado por separado |
| Ver evoluciones, perfil clínico o documentos ajenos | No | No | Sólo política global ya existente; pertenecer al consultorio no la amplía |
| Gestionar agenda, pacientes y prestaciones propias | Si también es profesional, desde su panel profesional | Sí, sólo propio | No aplica |

Las rutas administrativas consultan consultorio y cuenta a partir del usuario autenticado, nunca aceptan un `consultorio_id` arbitrario como autorización. Las rutas de turnos y clínica resuelven el `Profesional` de la sesión y verifican el ownership en servicio. Conocer un ID, tener rol `propietario` o ser parte de la misma cuenta no otorga acceso a registros clínicos.

### Invitación

El orden obligatorio es: (1) Valentina crea el profesional/perfil de actividad y programa sus módulos recurrentes; (2) la aplicación presenta el calendario y horarios autorizados; (3) Valentina emite invitación por correo o enlace; (4) el invitado acepta con una cuenta existente o crea su cuenta profesional individual; (5) al aceptar, la aplicación precarga esos días/horarios en la disponibilidad inicial del profesional.

La invitación tiene token aleatorio de alta entropía, hash en base, uso único, expiración inicial configurable de siete días, revocación y reserva provisional de plaza. La aceptación exige sesión autenticada y email verificado que coincida con el destinatario (o un registro que verifique ese correo antes de completar la asociación). El servidor reserva/consume cupos en transacción para que invitaciones concurrentes no excedan cuatro integrantes activos ni las plazas provisionales permitidas. Reenviar invalida tokens previos; aceptar/revocar repetidamente es idempotente o devuelve conflicto claro. La salida del equipo revoca membresía, no elimina cuenta ni datos.

Los horarios de la `Disponibilidad` profesional se intersectan siempre con las ocurrencias autorizadas. El profesional puede reducir o acomodar su disponibilidad propia, pero no ampliar módulos ni su recurrencia; toda creación y reserva valida el límite en backend. Actualizar el alquiler desde el panel de Valentina es el único mecanismo para ampliar las horas autorizadas.

El piloto requiere cuatro profesionales; el plan menciona cupos ampliables según la suscripción, pero el número de cupos para planes futuros y la semántica exacta de plazas ocupadas por invitaciones pendientes deben quedar parametrizados y aprobados antes de facturación comercial.

### Matrícula y actividad

No se debe inferir matrícula a partir de especialidad ni inventar una. El flujo pide la actividad y aplica su configuración de requisitos. Para actividades reguladas, matrícula y jurisdicción requeridas son explícitas; para estética sin requisito, la matrícula queda vacía y se habilitan prestaciones no clínicas sin especialidad médica obligatoria. Una actividad sin regla definida no se puede habilitar hasta que el propietario del producto la clasifique. Las validaciones de backend son la autoridad; los campos condicionales del frontend sólo mejoran la experiencia.

## Aislamiento de información clínica

Antes de activar los cuatro profesionales en un consultorio, cada lectura/escritura clínica debe filtrarse por `profesional_id` además de validar el vínculo profesional–paciente activo. Este alcance se aplica en servicios/repositorios y se demuestra con solicitudes negativas HTTP, incluidos IDs directos, cargas por token, endpoints de solicitudes de estudio y URLs de descarga.

- `EvolucionClinica` ya tiene autor; el listado profesional debe filtrar por `paciente_id` y el `profesional_id` de sesión. El administrador del consultorio no consulta evoluciones.
- `ClinicalProfile` debe cambiar de unicidad por paciente a unicidad por pareja `(paciente_id, profesional_id)` y conservar el profesional actualizador/autor. La lectura/edición de cada fila usa ambas claves.
- `PatientDocument` debe tener un propietario clínico explícito (profesional); `uploaded_by_profesional_id` por sí solo no identifica todos los documentos recibidos desde el paciente. Una carga vinculada a `StudyRequest` hereda/verifica el profesional de esa solicitud. Lista, descarga, confirmación y borrado filtran por propietario.
- `StudyRequest` y `StudyReview` conservan su profesional como owner; se valida que la review pertenezca al profesional de la solicitud y que todo documento enlazado respete el mismo alcance.
- Los datos de contacto/identificación básicos de `Paciente` pueden seguir siendo una identidad común vinculada mediante `ProfesionalPaciente`; no se devuelve esa lista al panel de la propietaria. No se comparte por ello el perfil, las evoluciones, solicitudes ni documentos.
- Una cuenta o rol de consultorio nunca se incorpora a excepciones de autorización clínica ni a endpoints de administrador global.

### Datos clínicos existentes y migración

El cambio de `ClinicalProfile` requiere resolver quién puede ver las filas actuales, que hoy son únicas por paciente. Propuesta: asignar cada perfil existente al profesional que figure como actualizador si esa relación sigue siendo válida; si falta o es ambigua, poner el registro en una cola/estado de revisión inaccesible para otros profesionales hasta una asignación explícita. No copiar un perfil a todos los profesionales asociados. Evoluciones y solicitudes ya incluyen profesional y pueden preservarlo; los documentos deben derivar ownership desde `StudyRequest` cuando exista, y los documentos sin autor/solicitud requieren revisión antes de hacerlos visibles bajo el nuevo filtro. La migración no debe ampliar visibilidad como efecto temporal.

La implementación deberá decidir antes del backfill qué hacer con filas huérfanas o ambiguas y validar conteos, consistencia y acceso previo/posterior en una copia sanitizada. No alterar datos clínicos productivos como parte de esta Fase 0.

## Panel de administración del consultorio

Un selector de contexto en la misma sesión ofrece **Mi panel profesional** y **Administración del consultorio** cuando el usuario tiene ambas membresías. La autorización sigue en backend y no depende de ocultar botones. El panel administrativo incluye:

- Resumen de salas, fecha, módulos libres/ocupados y duración configurada.
- Calendario de ocupación del recurso: intervalo, sala, estado y nombre del profesional asignado. No contiene nombre, email, motivo, prestación ni estado clínico del paciente.
- Alta/baja operativa de salas y configuración de duración para reservas nuevas.
- Invitaciones, estado de aceptación, reenvío/revocación y cupos.
- Alta/cancelación/reasignación de módulos con previsualización del impacto sobre turnos existentes y motivo auditado.
- Indicadores de disponibilidad general basados en módulos libres de sala; no una grilla con eventos de pacientes ni controles para modificar agendas de miembros.
- Estado de la suscripción y acceso a la administración de pago de la cuenta consultorio cuando esa integración se apruebe. El panel no redefine precios ni dispara cobros durante la etapa inicial.

La zona horaria se muestra como hora local del consultorio (`America/Argentina/Buenos_Aires` en el piloto) y se persiste un instante inequívoco. El routing manual del frontend actual debe integrarse sin asumir React Router.

## Suscripción y transición compatible

Usar la cuenta organizacional del consultorio como sujeto de una sola `Suscripcion`, reutilizando el flujo SaaS actual sólo después de diseñar el contrato de transición. No mezclar pagos clínicos de turnos con suscripción. La propietaria administra esa membresía y los métodos de pago.

En Fase 0 y en las entregas técnicas iniciales no se modifica la suscripción individual existente, precio, plan, trial ni cobro. La capa de consultorio se agrega sin mover `Profesional.cuenta_id` ni duplicar `Usuario`/`Profesional`. La activación comercial necesita una transición explícita que evite cobrar simultáneamente la suscripción individual y la del consultorio; preservar la cuenta individual no significa cobrar ambos planes. Se registrará el estado anterior, fecha, cuenta facturable y resultado del proveedor, con operación idempotente y recuperación ante webhook tardío. La forma de pausar, cancelar o mantener la cuenta individual exige aprobación del propietario y validación del proveedor antes de construir la transición.

## Roadmap por entregas

Las fases son incrementales. Ninguna requiere migrar o sembrar producción. La Fase 0 está cerrada funcionalmente; fechas no asignadas.

| Entrega | Dependencias | Alcance y aceptación |
|---|---|---|
| 0. Diseño funcional | Requisitos y decisiones del propietario recibidos | **CERRADA.** Arquitectura, permisos, recurrencia MVP, cambios, cupos, invitaciones, transición individual y criterios de operación documentados. |
| 1. Línea base y aislamiento clínico | Fase 0; antes de habilitar cualquier cuenta multi-profesional | Registrar línea base reproducible de pytest, Vitest, lint/build y Playwright; clasificar/reparar fallas existentes en cambios acotados. Después, aislar perfiles clínicos, evoluciones, documentos y estudios por profesional. Preserve autor inequívoco; restringir y revisar filas ambiguas. Pruebas negativas de backend y PostgreSQL. No habilitar miembros nuevos hasta pasar este gate. Primer plan: [`consultorio-01-baseline-y-aislamiento-clinico.md`](exec-plans/active/consultorio-01-baseline-y-aislamiento-clinico.md). |
| 2. Consultorio y catálogo de actividad | Entrega 1 | Modelos aditivos de organización/consultorio, salas, miembros y actividad profesional; cuatro integrantes activos iniciales, cupos configurables y preservación de cuentas/suscripciones individuales. Matrícula sólo según la regla aprobada para cada actividad. Pruebas de aislamiento de tenant. |
| 3. Reglas semanales e invitaciones | Entrega 2; aislamiento clínico aprobado | Valentina define profesional, días, uno o varios módulos por día y duración configurable (240 min inicial); ocurrencias concretas cubren horizonte móvil recomendado de 90 días. Crear/editar regla, excepción y expansión semanal con concurrencia PostgreSQL. Luego invita por email/enlace; cupo provisional, token hash, expiración 7 días configurable; al aceptar se crea o vincula cuenta profesional individual y se precarga disponibilidad propia dentro de los horarios autorizados. |
| 4. Turnos en ocurrencias autorizadas | Entregas 1–3 | Todos los canales de creación/reprogramación validan ocurrencia vigente, profesional asignado, rango y disponibilidad propia. El profesional no puede extender alquiler. Los turnos históricos individuales siguen operando. |
| 5. Cambios, solicitudes y excepciones | Entrega 4 | Cambio de fecha puntual, cambio recurrente desde fecha, módulo extraordinario, suspensión de día y reasignación sin conflicto. Si hay turnos afectados, Valentina sólo ve el conteo y puede solicitar resolución al profesional. El profesional resuelve desde su agenda; Valentina confirma y el backend recalcula conflictos. Sin cancelaciones/reprogramaciones automáticas. |
| 6. Paneles separados | Entregas 1–5 | Selector en la misma identidad; panel de consultorio para espacios, recurrencias, invitaciones y ocupación sin datos de pacientes; panel profesional conserva gestión de datos propios. No edición de agendas ajenas. E2E responsive y permisos API. |
| 7. Suscripción y preparación de piloto | Entregas anteriores; definición comercial para cobros | Suscripción única de consultorio visible para propietaria. Durante desarrollo se preservan las individuales y no se activan cobros ni se modifican precios. Antes del piloto: gates PostgreSQL/Playwright, WhatsApp/webhook, backup/restore, monitoreo, rollout y rollback aprobados. |

No habilitar multi-profesional hasta completar la Entrega 1. La recurrencia semanal concreta no se posterga ni se reemplaza por carga manual de ocurrencias: es parte de la Entrega 3 del MVP.

## Pruebas y criterios de aceptación

Las listas definen trabajo futuro. No se ejecutaron pruebas como parte de esta Fase 0.

### Backend unitario y API (SQLite donde sea compatible)

- Roles de propietaria/miembro, cuenta correcta, profesional activo, invitación expirada/revocada/usada, email no verificado, límite de cupo e IDs de otro consultorio.
- Matrícula requerida por actividad regulada, matrícula opcional en actividad de estética aprobada y prestación sin especialidad clínica.
- Perfiles clínicos separados por profesional; listados y mutaciones de evoluciones, perfil, documentos y estudios cruzados deniegan por HTTP 404/403 según contrato uniforme. Incluir propietario, recepcionista y admin de cuenta como sujetos negativos donde corresponda.
- Turno dentro y fuera de módulo, duración de prestación contra fin de módulo, módulo suspendido/cancelado, profesional incorrecto, reserva pública, reprogramación, enlaces de autogestión, pago/reapertura según flujo existente y cancelación repetida.
- Un profesional puede editar su disponibilidad sólo dentro de la autorización derivada de recurrencias/ocurrencias; al aceptar invitación sus días/horarios autorizados aparecen precargados. Un cambio de recurrencia no amplía disponibilidad sin autorización de Valentina.
- Cambios puntuales, versionado de recurrencia efectiva desde fecha, módulo extraordinario y suspensión; solicitud a profesional; respuesta administrativa contiene sólo conteo afectado; aprobación profesional obsoleta no evita el recálculo; confirmación propietaria falla si persiste cualquier turno afectado o conflicto.
- Cancelar, reasignar o cambiar intervalo de módulo con y sin turnos; no hay cascada; auditoría mantiene actor/motivo y no aparecen pacientes en DTOs administrativos.
- Cuenta individual actual y su panel, suscripción e inicio de sesión conservan su comportamiento anterior; transiciones repetidas no duplican asociaciones ni cobros simulados.

### PostgreSQL y concurrencia

- Alembic desde base vacía y desde el revision actual; extensiones/constraints y downgrade documentados.
- Dos módulos concurrentes solapados en misma sala: uno gana; salas diferentes o intervalos adyacentes: ambos ganan.
- Dos reglas semanales concurrentes incompatibles para la misma sala no pueden quedar activas aunque su primera fecha concreta esté fuera del horizonte materializado; reglas adyacentes o en salas separadas sí se aceptan.
- Dos generadores concurrentes para la misma serie/fecha producen una única ocurrencia; expansión repetida es idempotente. Dos excepciones/cambios concurrentes revalidan versión de regla y bloquean la sala.
- Ocurrencias semanales en la hora local del consultorio conservan el día/hora durante cambios DST, sin duraciones imposibles ni duplicados; probar también intervalos adyacentes y cruces de fecha según política aprobada.
- Dos reservas de turnos de profesionales distintos dentro de módulos que compiten por sala no pueden eludir la exclusión del módulo.
- Reprogramación de turno contra otra reserva, cancelación/cambio de módulo contra alta concurrente y aceptación concurrente de invitaciones/cupos. Verificar estado transaccional tras IntegrityError y respuesta HTTP 409 consistente.
- Consultas de ownership e índices con PostgreSQL, usando la suite CI requerida. SQLite no demuestra exclusión GiST ni semántica de bloqueo.

### Integración y Playwright

- Email de invitación en proveedor de prueba/in-memory, token de un uso, expiración, revocación, reenlace y aceptación de usuario existente/nuevo con email validado.
- Recorrido de cuatro cuentas sintéticas: Valentina cambia entre paneles; invita/acepta profesional; administra un módulo; profesional crea/reprograma/cancela turno en ese módulo; otro miembro no ve datos clínicos.
- Vista móvil/desktop de paneles, selector de contexto, calendario de salas, mensajes en español y ausencia de campos del paciente en respuestas/red.
- E2E de propietarios/profesionales usa PostgreSQL aislado y datos sintéticos; la limpieza sólo borra el recurso E2E creado para esa suite.
- Playwright: Valentina crea varios días y módulos por día, genera invitación después de configurar el horario, profesional acepta cuenta existente/nueva y ve disponibilidad inicial autorizada; intenta ampliar fuera de alquiler (rechazo API); la propietaria solicita cambio con conteo privado, el profesional resuelve turnos y la confirmación vuelve a validar.

### Verificación real previa a lanzamiento

- Probar invitación y operación con cuentas sintéticas autorizadas. No usar historias ni pacientes reales para demostrar aislamiento.
- WhatsApp: los tests actuales de consentimiento/idempotencia/webhook son simulados. Registrar una prueba real dirigida sólo a un destinatario autorizado, comprobar entrega/estado de fallo y acción por enlace; no ejecutar el worker amplio. Persistir estados de webhook con idempotencia antes de declarar entrega.
- Backups: auditoría encuentra dumps con checksum, pero programación privilegiada y restauración siguen **NO DETERMINADAS**. Identificar cron/timer realmente activo y ensayar restauración desde dump en entorno aislado; documentar alertas/retención antes de piloto.
- No considerar una respuesta simulada de Meta, correo en memoria o fixture como evidencia real de entrega.

### Baseline de validaciones observado por la auditoría

La auditoría informa `verify.ps1 -Full` fallido; `pytest -q` con 872 pasados, 26 omitidos y una falla dependiente de la fecha en `test_metricas_de_adopcion_calculan_estado_conteos_y_dias_activos`; Vitest con 406 pasados y un timeout de cinco segundos en `agendaProfesionalIntegracion.test.tsx` (la repetición aislada pasó); Playwright con 4/7, tres fallas (fixture de captura no verificado por email y dos textos de ayuda desactualizados). También registra `npm audit --omit=dev` con una alerta alta y una baja corregibles.

Antes de usar las suites como gate de esta feature, registrar una línea base y corregir o clasificar esas fallas en cambios acotados. La fase 0 no las reejecuta ni las trata como arregladas. Mantener los gates Backend CI, PostgreSQL CI y Frontend CI existentes; Playwright E2E CI sigue informativo según la documentación actual hasta que se cumpla su umbral de estabilidad.

## Migración reversible y despliegue seguro

Aplicar un enfoque **expandir → migrar → restringir**, compatible con PostgreSQL y con la API anterior:

1. Crear tablas nuevas sin cambiar rutas existentes. Añadir referencias nuevas inicialmente nullable. No renombrar `mediturnos`/`MediTurnos` ni alterar identificadores históricos. Preservar íntegramente cuentas y suscripciones individuales durante todo el desarrollo.
2. Ensayar Alembic en PostgreSQL vacío y en un dump sanitizado del esquema actual. Medir perfiles clínicos/documentos sin owner; no asignar ni copiar en silencio datos ambiguos.
3. Desplegar código de lectura compatible con valores nulos/históricos y bajo feature flag. No activar asociación de cuatro profesionales hasta completar aislamiento clínico.
4. Backfill sólo asociaciones cuyo owner sea demostrable, en transacciones/reanudable y con conteos de control. Restringir filas sin owner verificable y registrarlas para revisión; no exponerlas por fallback. Ejecutar verificación de integridad antes de agregar `NOT NULL`, claves y exclusiones.
5. Habilitar primero en staging con la cuenta/sala sintéticas; probar alta, solape, cancelación, reprogramación, aislamiento y restauración. No migrar, seedear ni probar mutaciones en producción durante esta etapa.
6. Preparar rollout limitado, respaldo PostgreSQL con checksum y restore verificado, health checks, monitoreo y responsable de rollback antes de cualquier release productivo. La autorización para producción será una decisión separada y explícita.
7. Mantener el código viejo leyendo turnos sin módulo. El rollback de aplicación desactiva el flag y vuelve a rutas individuales; no se elimina información nueva. Las migraciones de datos no se revierten destructivamente. Para devolver esquema, primero hacer backup/export de datos de consultorio y usar downgrade sólo si las constraints nuevas no contienen datos irreconciliables. Nunca volver a una base anterior perdiendo escrituras posteriores.
8. Separar transición de suscripción: no iniciar, cancelar ni reemplazar cobros desde la migración técnica. Hacer una transición comercial auditada, idempotente y coordinada con el proveedor, con estado recuperable ante webhook tardío.

La migración reversible significa poder volver al comportamiento anterior sin pérdida de datos; no promete revertir una operación de pago externa ni eliminar de forma segura datos clínicos ya creados.

## Riesgos y mitigaciones

| Riesgo | Mitigación/gate |
|---|---|
| Filtración de información clínica por joins/IDs directos o documentos cargados por paciente | Owner por profesional en cada recurso; filtros en service/repository; pruebas negativas API para rutas y descargas; no habilitar equipo antes del gate clínico. |
| Doble asignación concurrente de sala | Restricción PostgreSQL GiST en módulo y pruebas concurrentes en CI PostgreSQL; no confiar en consulta previa de disponibilidad. |
| Turnos huérfanos por cancelar, reasignar o cambiar módulo | Bloqueo transaccional, conflicto explícito, traslado validado y auditado; no cascadas destructivas. |
| Romper cuentas/suscripciones individuales o cobrar doble | Membresía consultorio separada, backfill aditivo, feature flag y gate comercial/proveedor antes de transición. |
| Prestador no clínico obligado a presentar matrícula falsa | Catálogo de actividad con regla explícita; matrícula/especialidad opcionales sólo donde esté aprobado. |
| Módulo con zona horaria o DST ambiguos | Guardar instantes con tz y zona IANA del consultorio; definir manejo de horas locales inexistentes/repetidas y probar Argentina/Buenos Aires. |
| Invitaciones filtradas/reusadas o exceso de cupo concurrente | Token hash de un uso, expiración, verificación de email, límite transaccional, rate limit y logs sin secreto. |
| Webhook aceptado interpretado como entrega WhatsApp | Estados persistidos reconciliados, firma validada, idempotencia y prueba real dirigida; proveedor puede aceptar y luego informar fallo. |
| Backups sin restauración demostrada | Identificar cron privilegiado y restaurar un dump con checksum en entorno aislado antes de lanzamiento. |
| Línea base ya inestable | Corregir/aislar prueba de fecha, timeout Vitest, fixture E2E, dos aserciones de ayuda y alertas de dependencias antes de establecer nuevos gates. |

## Decisiones aprobadas y pendientes

El propietario aprobó el diseño general y cerró estas reglas funcionales:

- El profesional y su horario de uso se configuran antes de invitar. Invitación por email o enlace; el profesional acepta con cuenta existente o crea una cuenta profesional individual.
- La agenda autorizada queda precargada al aceptar. Puede administrar sus prestaciones, turnos, pacientes e historia propia; su disponibilidad efectiva queda limitada a los módulos. Sólo Valentina amplía o cambia alquileres.
- Recurrencia semanal forma parte del MVP; varios días y módulos por día, duración predeterminada configurable de cuatro horas, ocurrencias concretas, una sala inicial y diseño multi-sala.
- Cambios puntuales, desde fecha, extras, suspensiones y reasignación sin conflicto. Si hay turnos afectados, la propietaria sólo recibe el conteo; puede pedir al profesional resolverlos. El profesional marca la solicitud resuelta y Valentina confirma después de una nueva validación del servidor. No hay cancelación/reprogramación automática.
- No existe acceso cruzado a historias clínicas. Registros con propietario inequívoco se conservan; registros sin propietario se restringen para revisión.
- Catálogo de actividad y matrícula condicional; cuatro integrantes activos iniciales, cupos parametrizados, invitación pendiente con reserva provisional y vencimiento inicial configurable de siete días.
- Durante el desarrollo se preservan cuentas/suscripciones individuales; no se activan cobros ni se cambian precios públicos. Primero se registra la línea base y el aislamiento clínico precede a habilitar miembros múltiples.

### Bloqueos efectivos de la primera entrega

La primera entrega se limita a la línea base y el aislamiento clínico (ver [primer plan de implementación](exec-plans/active/consultorio-01-baseline-y-aislamiento-clinico.md)). **No queda una decisión funcional del propietario pendiente que impida empezarla.** Las reglas de backfill ya aprobadas permiten conservar lo atribuible y mantener inaccesible lo ambiguo hasta su revisión.

Sí bloquean la aceptación completa de esa entrega y, por tanto, abrir el acceso multi-profesional:

1. **Antes del backfill de un entorno con datos reales:** inspeccionar una copia sanitizada y clasificar qué perfiles/documentos tienen propietario inequívoco. Esta entrega sólo validó la lógica con filas sintéticas; no accedió a datos reales. Las filas sin evidencia permanecen restringidas.
2. **Cierre de integración:** esperar CI del PR. La suite Vitest completa tuvo un fallo intermitente de carga en `adminAdoption.test.tsx` (406/407), mientras que la repetición focalizada pasó (3/3); la suite completa debe quedar verde en CI antes de integrar. No habilitar membresías múltiples hasta confirmar todos los gates.

No bloquean esa primera entrega, pero sí su fase específica: el catálogo concreto de actividades/matrículas para completar altas (Entrega 2/3); la semántica de cancelación comercial de alquileres; los términos/precio y momento de migrar suscripciones individuales (Entrega 7); y la aceptación de gates operativos de WhatsApp/webhook y backup/restauración para preparar el piloto (Entrega 7). Los cobros y cambios de precio siguen expresamente fuera del trabajo actual.

## Cierre de Fase 0

- Diseño general y reglas funcionales adicionales aprobados por el propietario.
- Diseño aprobado y Entrega 01 en implementación/revisión; no se habilitan miembros múltiples.
- La migración se validó sólo con PostgreSQL y datos sintéticos. No se modificaron datos clínicos reales, cobros ni producción.
