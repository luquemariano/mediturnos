# Seguridad de Turnelia

Estado: **ACTUAL**, basado en código, configuración, tests y documentación revisada. No es una auditoría ofensiva.

## Autenticación

- La API usa Bearer JWT; algoritmo, secreto y expiración son configurables.
- El frontend conserva el token en `localStorage` como `access_token`.
- Las contraseñas se procesan con `pwdlib` y no deben registrarse.
- Existen login, cambio de contraseña, `forgot-password` y `reset-password`.
- Los tokens de recuperación tienen expiración y uso controlado por el servicio.
- Hay rate limiting configurable para registro, login y recuperación. La clave se forma con el nombre de la operación y la IP del cliente. Por defecto se usa `request.client.host`; con `TRUST_PROXY_HEADERS=true` se intenta usar el primer valor válido de `X-Forwarded-For` y, si no es una IP válida, se conserva la IP directa. Por tanto, detrás de un proxy la identificación depende de esa configuración; una configuración incorrecta puede afectar la identificación del cliente.

## Roles y ownership

- **administrador:** cuentas y operaciones administrativas autorizadas.
- **recepcionista:** pacientes, agendas y catálogos según permisos.
- **profesional:** su perfil, agenda, disponibilidad, prestaciones y pacientes relacionados.
- **paciente:** sus propios recursos según endpoint, ownership y contexto.

La autorización se aplica mediante dependencias FastAPI y comprobaciones en routers/servicios. Los profesionales no deben asumir acceso global a pacientes o agendas. El acceso autenticado a documentos clínicos depende de roles y relaciones autorizadas.

## Endpoints y tokens públicos

Health checks, login, registro, recuperación, webhooks de Mercado Pago, acciones de confirmar/cancelar turnos y carga pública de estudios pueden ser públicos o no requerir sesión convencional. Usan validaciones propias: los tokens públicos no sustituyen autorización autenticada y los webhooks deben validar firma y referencias.

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
