# Seguridad de Turnelia

Estado: **ACTUAL**, basado en código, configuración, tests y documentación revisada. No es una auditoría ofensiva.

## Autenticación

- La API usa Bearer JWT; algoritmo, secreto y expiración son configurables.
- El frontend conserva el token en `localStorage` como `access_token`.
- Las contraseñas se procesan con `pwdlib` y no deben registrarse.
- Existen login, cambio de contraseña, `forgot-password` y `reset-password`.
- Los tokens de recuperación tienen expiración y uso controlado por el servicio.
- Hay rate limiting configurable para registro, login y recuperación. La clave se forma con el nombre de la operación y la IP del cliente. Por defecto se usa `request.client.host`; con `TRUST_PROXY_HEADERS=true` se intenta usar el primer valor válido de `X-Forwarded-For` y, si no es una IP válida, se conserva la IP directa. Por tanto, detrás de un proxy la identificación depende de esa configuración; una configuración incorrecta puede afectar la identificación del cliente.
- Las rutas públicas de disponibilidad, creación, consulta, cancelación y reprogramación usan buckets separados. Los eventos de rate limit registran únicamente el scope, nunca la IP completa, el token ni el cuerpo de la petición. `TRUST_PROXY_HEADERS=true` sólo debe habilitarse detrás de un proxy confiable (por ejemplo, Caddy configurado para sobrescribir X-Forwarded-For). Antes de producción se deben auditar/redactar los access logs de `/public/reservas/{token}` porque el token bearer viaja en la URL.
- Los endpoints públicos de ofertas waitlist también transportan el token en la URL. En producción, el arranque de Uvicorn usa `--no-access-log`; los logs de aplicación no incluyen el token. Caddy no declara access log habilitado en este repositorio.
- El alta pública de waitlist usa `POST /public/profesionales/{slug}/waitlist`, sólo acepta prestaciones públicas habilitadas, limita a 10 solicitudes por minuto/IP y responde sin IDs internos ni existencia de otras entradas. Los errores de duplicado se presentan con un mensaje genérico.

## Roles y ownership

- **administrador:** cuentas y operaciones administrativas autorizadas.
- **recepcionista:** pacientes, agendas y catálogos según permisos.
- **profesional:** su perfil, agenda, disponibilidad, prestaciones y pacientes relacionados.
- **paciente:** sus propios recursos según endpoint, ownership y contexto.

La autorización se aplica mediante dependencias FastAPI y comprobaciones en routers/servicios. Los profesionales no deben asumir acceso global a pacientes o agendas. El acceso autenticado a documentos clínicos depende de roles y relaciones autorizadas.

### Consultorio (fundación en rama; no desplegada)

- El acceso administrativo se concede por `ConsultorioAdministrador`, independiente de roles globales y de `CuentaUsuario`.
- La API resuelve la relación del usuario con el consultorio en cada petición; los IDs enviados por cliente no autorizan recursos. Los consultorios y salas ajenos responden 404.
- `ConsultorioProfesional` no cambia la cuenta individual, el ownership profesional ni las rutas clínicas. La propietaria de un consultorio conserva únicamente el alcance clínico de su propio perfil profesional.
- No hay acceso clínico compartido por pertenecer a un mismo consultorio. Las pruebas negativas HTTP usan IDs conocidos para verificar perfiles, evoluciones, documentos y solicitudes de estudios; también comprueban que el rol profesional no obtiene la lista general de pacientes ni la agenda administrativa.
- No hay rutas para invitar, activar integrantes o ampliar la relación profesional; tampoco para editar agendas ajenas.

### Consultorio (módulos e invitaciones en rama de Entrega 04)

- Cada mutación/respuesta administrativa resuelve `ConsultorioAdministrador` por usuario autenticado; IDs de consultorio, sala, regla u ocurrencia no autorizan acceso y los recursos ajenos responden 404.
- Las ocurrencias administrativas sólo devuelven sala, intervalo, estado y profesional asignado. No incluyen turno, paciente, prestación ni metadatos clínicos.
- Reglas de sala se serializan bloqueando la fila de sala; expansión recurrente serializa por fila de regla y clave única regla/fecha. La exclusión GiST PostgreSQL `[)` protege los intervalos activos ante carreras y conserva adyacencia válida.
- Alta y reprogramación comparten la verificación de módulo para profesionales vinculados. La reserva bloquea la ocurrencia validada; suspensión/cambio bloquean esa misma fila antes del conteo y no cancelan ni reprograman turnos automáticamente.
- Si un cambio afecta turnos `reservado`/`confirmado`, la operación se rechaza y sólo revela un conteo agregado; la auditoría no guarda IDs de turnos ni pacientes. La revisión de tests cubre negativas HTTP y concurrencia PostgreSQL con datos sintéticos.
- La expansión del horizonte ocurre al consultar módulos o al reservar/reprogramar. No existe worker de materialización; la reserva extiende el horizonte transaccionalmente antes de validar.
- `/profesionales/me/consultorio/modulos` deriva la identidad desde el JWT y el perfil profesional asociado; el repositorio vuelve a filtrar por `usuario_id`, vínculo `preparatorio`/`activo`, consultorio/sala activos y ocurrencia activa, sin aceptar IDs de pertenencia enviados por el cliente. Respuesta allowlist: sala, inicio, fin y estado; la ruta no escribe ni expande recurrencias. Los profesionales no autorizados a administrar reciben 404 en endpoints del consultorio y el endpoint profesional no define verbos de mutación.
- La preparación y gestión de invitaciones exige `ConsultorioAdministrador`; el backend no crea usuarios, perfiles profesionales, matrículas, pacientes ni datos clínicos para la persona invitada sin cuenta.
- El cupo se serializa bloqueando la fila `consultorios`; cuenta perfiles activos distintos (incluida la titular) y las invitaciones en preparación/pendientes no vencidas. Un índice parcial evita duplicar email invitado activo en el consultorio. Las ocurrencias pendientes siguen `activas` y participan de la misma exclusión GiST de sala.
- El token se genera con entropía criptográfica, se guarda sólo como hash y no vuelve en respuestas administrativas. El enlace lo lleva en el fragmento `#` del navegador, que no se envía en la petición HTTP. El frontend conserva el token sólo en memoria; el reenvío rota el hash anterior y revocar/vencer lo invalida. El hash aceptado se conserva para permitir el reintento idempotente del mismo usuario autenticado.
- Aceptar exige rol profesional, email autenticado/verificado coincidente y perfil existente. La aplicación bloquea consultorio e invitación y efectúa vínculo y reasignación en una transacción. Errores de token inválido, vencido, revocado o email distinto son genéricos. Cuenta nueva: registro individual en pestaña separada y retorno al enlace original, sin handoff server-side persistido. El formulario individual exige matrícula y especialidad; el alta de actividades que no las requieren queda fuera de esta entrega.
- Al revocar o vencer se invalidan los tokens y las ocurrencias activas futuras dejan de ocupar sala; la exclusión GiST también protege frente a carreras. La administración sólo puede gestionar plazas y horarios: no obtiene agendas, pacientes ni registros clínicos de otros profesionales.

## Endpoints y tokens públicos

Health checks, login, registro, recuperación, webhooks de Mercado Pago, acciones de confirmar/cancelar turnos y carga pública de estudios pueden ser públicos o no requerir sesión convencional. Usan validaciones propias: los tokens públicos no sustituyen autorización autenticada y los webhooks deben validar firma y referencias.

La baja de novedades usa un token firmado de propósito específico ligado al ID del usuario y con vencimiento de 30 días. El GET sólo muestra una confirmación; el cambio persistente se realiza en el POST final. Los endpoints de campañas y del catálogo de novedades requieren administrador global. Las campañas sólo seleccionan usuarios profesionales y no consultan datos clínicos.

## Logging

En acciones públicas de turnos se registran eventos técnicos como motivo de token inválido, reprogramación y acción aplicada, sin que los mensajes observados incluyan el token. El worker de recordatorios registra inicio/fin, conteos de elementos generados/procesados, configuración no secreta como proveedor y zona horaria, y errores operativos mediante excepciones. Los errores de recordatorio también pueden conservarse truncados en el estado interno del recordatorio.

Se puede registrar:

- identificadores técnicos y nombres de eventos necesarios para operar;
- acciones, estados, conteos y errores operativos o de validación no sensibles.

No debe registrarse:

- contraseñas;
- JWT completos;
- tokens de acción pública, recuperación u otros tokens secretos;
- credenciales o secretos de integración;
- contenido clínico sensible.

La ausencia de un token en los mensajes revisados no debe interpretarse como una garantía global para todos los logs del sistema.

## Datos sensibles

- No exponer contraseñas, JWT, tokens, secretos de webhook ni credenciales.
- Evoluciones, perfiles clínicos, documentos y solicitudes de estudios son información sensible.
- Evitar logs con datos de pacientes o autenticación.
- `.env`, dumps y backups locales no deben incorporarse a documentación ni Git.

## Integraciones

- Mercado Pago separa pagos clínicos y suscripciones SaaS, con flujos y variables diferentes.
- Resend es configurable; API key, remitente y entrega productiva no están verificados.
- R2 es storage configurable; su uso productivo es **NO DETERMINADO**.
- Acciones tokenizadas deben limitarse al recurso y acción representados por el token.

## Riesgos y límites conocidos

- El frontend almacena el JWT en `localStorage`.
- SQLite en tests no equivale a PostgreSQL.
- Los endpoints públicos requieren validación de tokens o firmas.
- La coexistencia de flujos Mercado Pago puede confundir configuración y permisos.
- El estado operativo de infraestructura y proveedores externos es **NO DETERMINADO**.
