# Producto Turnelia

Turnelia es una aplicación web para gestionar agendas y turnos médicos. Este documento se limita a comportamientos deducibles del código, modelos, schemas y tests.

## Actores

- **Administrador:** gestiona cuentas, catálogos y operaciones administrativas autorizadas.
- **Recepcionista:** opera pacientes, agendas, disponibilidades y turnos según permisos.
- **Profesional:** gestiona perfil, prestaciones, disponibilidad, pacientes, agenda, onboarding y revisión clínica.
- **Paciente:** accede a su perfil, turnos, pagos y solicitudes propias según los endpoints disponibles. El acceso autenticado a documentos clínicos está restringido a los roles y relaciones autorizados; la carga pública de estudios es un flujo separado mediante token.

## Módulos y reglas

| Módulo | Función comprobable | Restricciones relevantes |
|---|---|---|
| Profesionales | Perfil, prestaciones, disponibilidad, pacientes y agenda | Principalmente recursos propios |
| Pacientes | Alta, asociación, perfil e historial de turnos | Rol y ownership |
| Especialidades | Catálogo profesional | Migración de 36 especialidades |
| Prestaciones | Servicios con duración/precio | Participan en disponibilidad y pagos |
| Disponibilidad | Horarios, excepciones y feriados | Considera zona horaria |
| Turnos | Gestionar citas según actor, ownership y contexto del endpoint | Las acciones de crear, confirmar, cancelar o reprogramar no son uniformes para todos los actores; se aplican permisos, estado, disponibilidad y solapamientos |
| Evoluciones clínicas | Registrar evolución | Información sensible y acceso restringido |
| Perfiles clínicos | Información clínica estructurada | Acceso controlado |
| Documentos | Asociar y consultar archivos clínicos | Acceso autenticado sólo para roles/relaciones autorizados; storage configurable |
| Solicitudes de estudios | Solicitar y revisar estudios | Relación profesional-paciente |
| Carga pública de estudios | Cargar y enviar estudios sin sesión mediante token | Es distinto del acceso autenticado a documentos clínicos; token y validaciones |
| Notificaciones | Consultar y marcar avisos | Centro privado autenticado |
| Recordatorios | Email y acciones confirmar/cancelar | Worker, cron y email |
| Pagos clínicos | Cobrar prestaciones de turnos | Webhook, monto, moneda, referencia e idempotencia |
| Suscripciones SaaS | Gestionar suscripción de cuenta | Flujo Mercado Pago separado |
| Onboarding | Guiar alta profesional | Pasos de perfil, prestaciones y disponibilidad |

El nombre comercial actual es **Turnelia**. `mediturnos`/`MediTurnos` permanece como identidad técnica o histórica; no debe renombrarse automáticamente.
