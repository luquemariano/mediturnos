# Turnelia — guía operativa para contribuidores y agentes

## Identidad

**Turnelia** es el nombre comercial actual. El repositorio conserva `mediturnos` y `MediTurnos` como nombres técnicos o históricos. No renombrar identificadores internos sólo por branding; cualquier limpieza de naming requiere una tarea específica y controlada.

## Mapa rápido

- Backend: FastAPI, SQLAlchemy, Pydantic, Alembic, JWT y PostgreSQL.
- Frontend: React, TypeScript, Vite, Axios y CSS propio.
- Capas backend: `router → service → repository` cuando corresponde.
- Infraestructura declarada: Docker, Render, PostgreSQL y Render Cron; operación real NO DETERMINADA desde el repositorio.
- Integraciones implementadas/configurables: Mercado Pago, Resend y Cloudflare R2; operación productiva NO DETERMINADA.
- Tests backend: pytest, habitualmente sobre SQLite; esto no demuestra por sí solo compatibilidad PostgreSQL.

## Documentación canónica

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): estructura y flujos técnicos actuales.
- [`docs/PRODUCT.md`](docs/PRODUCT.md): módulos, actores y reglas de producto deducibles del sistema.
- [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md): estado comprobable, límites y deuda conocida.
- [`docs/DECISIONS.md`](docs/DECISIONS.md): decisiones técnicas demostrables y revisables.
- [`docs/WORKFLOW.md`](docs/WORKFLOW.md): forma de trabajo con agentes.
- [`docs/SECURITY.md`](docs/SECURITY.md): autenticación, autorización y datos sensibles.
- [`docs/TESTING.md`](docs/TESTING.md): comandos, cobertura y limitaciones de validación.
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md): Render, Aiven, variables e integraciones declaradas.
- [`docs/ROADMAP.md`](docs/ROADMAP.md): trabajo pendiente y estado del Harness.

Consultar primero este archivo; luego el documento específico de la tarea.

## Reglas de trabajo

- Preservar cambios ajenos y archivos no relacionados.
- No exponer ni registrar contraseñas, JWT, tokens, secretos de webhooks ni datos sensibles de pacientes.
- No hacer checkout, merge, commit, push ni Git destructivo salvo autorización explícita.
- Usar Alembic para cambios persistentes; no confiar en `create_all()` para producción.
- Mantener compatibilidad PostgreSQL aunque los tests usen SQLite.
- Mantener permisos en el router y ownership en la lógica de negocio.
- Mantener el texto visible al usuario en español, salvo contexto existente.
- Respetar la separación router/service/repository cuando corresponda al flujo existente.
- No ejecutar migraciones ni seed salvo que la tarea lo pida.

## Integraciones y dominios

Los pagos clínicos de turnos y las suscripciones SaaS son flujos distintos y no deben asumirse equivalentes. Resend gestiona emails transaccionales; Cloudflare R2 es almacenamiento opcional; Render Cron procesa recordatorios de turnos.

## Antes de implementar una feature

1. Leer `AGENTS.md` y la documentación relacionada.
2. Inspeccionar código, configuración y tests existentes.
3. Identificar compatibilidad, permisos y ownership afectados.
4. Planificar e implementar el cambio mínimo.
5. Validar con tests/lint/build proporcionales al riesgo.
6. Actualizar documentación y comunicar cambios, riesgos y límites.

## Fuente de verdad

El orden de confianza es: código/configuración real, tests, migraciones, documentación verificada e inferencias explícitamente marcadas como `NO DETERMINADO`.
