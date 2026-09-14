# Turnelia

<p align="center">
  <img src="frontend/public/brand/mediturnos-logo-horizontal.svg" alt="Turnelia" width="320">
</p>

<p align="center">SaaS de gestión de turnos y operación para profesionales y consultorios.</p>

<p align="center"><strong>FastAPI · React · TypeScript · PostgreSQL · Docker · JWT</strong></p>

Turnelia es un producto web en producción para administrar profesionales, pacientes, prestaciones, disponibilidad, agenda, turnos y procesos clínicos y comerciales. El repositorio conserva `mediturnos`/`MediTurnos` como nombres técnicos e históricos.

## Estado del proyecto

**Estado de documentación: septiembre de 2026.** Turnelia está desplegado productivamente en un VPS OVH con Ubuntu 24.04. La aplicación pública utiliza [turnelia.com.ar](https://turnelia.com.ar), la API utiliza [api.turnelia.com.ar](https://api.turnelia.com.ar) y el estado operativo documentado está respaldado por un cutover y verificaciones posteriores.

La producción actual usa Docker Compose, PostgreSQL 18, Caddy, Cloudflare, Resend, Mercado Pago y cron del host para recordatorios. Consultá [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md), [`docs/OPERATIONS_VPS.md`](docs/OPERATIONS_VPS.md) y [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md).

## Funcionalidades

### Gestión profesional

- Registro, verificación de email, autenticación y recuperación de contraseña.
- Onboarding de profesionales: perfil, prestaciones y disponibilidad.
- Pacientes, asociaciones, agenda con vistas día/semana/mes y excepciones horarias.
- Creación, confirmación, cancelación y reprogramación de turnos, con validación de disponibilidad y solapamientos.
- Evoluciones y perfil clínico con permisos y ownership.
- Solicitudes de estudios, revisión profesional y carga pública mediante enlaces con token.
- Notificaciones privadas y acciones controladas sobre turnos.

### Reserva online pública

- Página pública por slug del profesional: `/reservar/<slug>`.
- Prestaciones habilitadas, disponibilidad pública y creación de reservas.
- Autogestión pública mediante identificadores y tokens no enumerables.
- Validaciones de disponibilidad, conflictos y límites de uso en endpoints públicos.
- Enlace reutilizable para compartir la reserva, con soporte de WhatsApp y QR en la interfaz.

### Lista de espera

La base de lista de espera, matching de candidatos, ofertas con vencimiento, worker y aceptación pública están implementados en código y cubiertos por tests. La experiencia completa continúa **EN CURSO / PENDIENTE DE REVALIDACIÓN EN EL ENTORNO OBJETIVO**. WhatsApp, SMS, push, IA y reporting no forman parte del alcance actual.

### Cuenta y seguridad

- JWT Bearer y roles `administrador`, `recepcionista`, `profesional` y `paciente`.
- Verificación y reenvío de email; recuperación y cambio de contraseña.
- Restricciones de rol y ownership en recursos protegidos.
- Rate limiting configurable para registro, login, recuperación y endpoints públicos.
- Tracking de login y eventos de actividad sin exponer información clínica sensible.
- En producción se deshabilitan Swagger, ReDoc y OpenAPI público; los secretos se cargan mediante variables de entorno.

### SaaS, pagos y automatizaciones

- Suscripciones SaaS con planes, trial, estados, sincronización, cancelación y webhooks de Mercado Pago.
- Pagos clínicos de turnos mediante un flujo separado de las suscripciones SaaS.
- Emails transaccionales mediante Resend; recuperación de contraseña verificada en producción.
- Recordatorios automáticos por email, procesados por un worker cada 15 minutos mediante cron del VPS.

### Analítica y SEO

- GA4 se carga en producción mediante `gtag` y registra page views y eventos definidos en el frontend.
- PostHog está integrado para Product Analytics, Web Analytics y Session Replay en la región EU. Usa allowlist de eventos y propiedades, elimina PII y no llama a `identify`; ver [`docs/POSTHOG.md`](docs/POSTHOG.md).
- Landing, páginas legales y Centro de Ayuda con metadata, canonical, robots, OpenGraph, Twitter Cards y JSON-LD donde corresponde.
- Sitemap público en [`frontend/public/sitemap.xml`](frontend/public/sitemap.xml) y reglas en [`frontend/public/robots.txt`](frontend/public/robots.txt).
- No se encontró integración de Clarity en el repositorio.

## Arquitectura actual

```text
Internet → Cloudflare DNS → Caddy / TLS en VPS OVH
                              ├─ Frontend React/Vite + Nginx (Docker)
                              └─ API FastAPI/Uvicorn (Docker)
                                      └─ PostgreSQL 18 (Docker, red interna)

API ── Resend (email) · Mercado Pago (pagos/suscripciones)
Frontend ── GA4 / PostHog · Cron ── worker de recordatorios
```

En el backend, el flujo habitual es `router → service → repository → SQLAlchemy/PostgreSQL`. Alembic mantiene el esquema. Los tests usan SQLite en muchos casos y cuentan con suites selectivas contra PostgreSQL; SQLite no sustituye la validación completa del motor productivo.

## Stack tecnológico

- **Frontend:** React 19, TypeScript, Vite, Axios, CSS propio, Vitest, Testing Library y Playwright.
- **Backend:** Python 3.14, FastAPI, SQLAlchemy, Pydantic, Alembic, Uvicorn, JWT y `pwdlib`.
- **Datos e infraestructura:** PostgreSQL 18, Docker, Docker Compose, Nginx, Caddy, Cloudflare DNS y cron del host. Producción en OVH; compose local con PostgreSQL 17.
- **Integraciones:** Mercado Pago, Resend, GA4 y PostHog. R2 es configurable, pero producción mantiene `OBJECT_STORAGE_PROVIDER=fake`; no es storage productivo verificado.

## Estructura del repositorio

```text
mediturnos/
├── app/                # core, models, routers, schemas, services, scripts
├── alembic/            # migraciones
├── frontend/           # UI, API, SEO, analytics, ayuda y tests
├── tests/              # backend y PostgreSQL seleccionados
├── docs/               # producto, operación, arquitectura y roadmap
├── docker-compose.yml  # desarrollo local
├── docker-compose.vps.yml
├── docker-compose.e2e.yml
├── Dockerfile
├── verify.ps1
└── README.md
```

## Desarrollo local

Requisitos: Git, Python 3.14, Node.js/npm y Docker. Para una instalación reproducible, consultá [`docs/WORKFLOW.md`](docs/WORKFLOW.md) y [`docs/TESTING.md`](docs/TESTING.md).

```bash
git clone https://github.com/luquemariano/mediturnos.git
cd mediturnos
cp .env.example .env
docker compose --env-file .env up -d --build
```

La API queda en `http://127.0.0.1:8000`; en desarrollo Swagger está en `/docs`. El arranque ejecuta `alembic upgrade head` antes de Uvicorn. Para el frontend:

```bash
cd frontend
npm ci
npm run dev
```

La aplicación queda en `http://localhost:5173`. El seed demo requiere `APP_ENV=demo` y `DEMO_SEED_ENABLED=true`; nunca se ejecuta en producción.

## Testing y calidad

```powershell
.\verify.ps1 -Quick
.\verify.ps1 -Full
.\verify.ps1 -E2E
```

También existen `python -m pytest`, `npm test`, `npm run lint`, `npm run build` y `npm run test:e2e`. GitHub Actions separa backend, frontend, PostgreSQL y Playwright E2E. E2E usa PostgreSQL aislado en Docker y su job es informativo. Ver [`docs/TESTING.md`](docs/TESTING.md).

## Producción y observabilidad

La producción usa `docker-compose.vps.yml` en `/srv/apps/turnelia`, con frontend, API y PostgreSQL en Docker; Caddy termina TLS y enruta los dominios públicos. `/health/live` y `/health/ready` están disponibles para sondas. El health check del VPS revisa contenedores, API, base, cron, reminders, backups, UFW y Fail2ban.

Se ejecutan backups diarios con `pg_dump`, checksum SHA256 y retención local documentada de 14 días. No se incluyen IPs, accesos SSH, credenciales ni secretos.

## Seguridad

La aplicación valida configuración de producción, exige PostgreSQL y un secreto JWT válido, restringe CORS, limita endpoints sensibles y evita herramientas de desarrollo expuestas. Los documentos y datos clínicos requieren autorización según rol y relación. Estas medidas no constituyen una certificación normativa.

## Documentación

- [`docs/PRODUCT.md`](docs/PRODUCT.md): actores, módulos y reglas.
- [`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md): estado funcional y evidencia operativa.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): arquitectura lógica y límites.
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md): deployment OVH, dominios, Caddy y servicios.
- [`docs/OPERATIONS_VPS.md`](docs/OPERATIONS_VPS.md): runbook operativo.
- [`docs/POSTHOG.md`](docs/POSTHOG.md): analítica y privacidad.
- [`docs/TESTING.md`](docs/TESTING.md): comandos, CI y limitaciones.
- [`docs/F11_HELP_CENTER_AUDIT.md`](docs/F11_HELP_CENTER_AUDIT.md): auditoría del Centro de Ayuda.
- [`docs/MIGRATION_RENDER_AIVEN_TO_OVH.md`](docs/MIGRATION_RENDER_AIVEN_TO_OVH.md): historia del cutover.
- [`docs/ROADMAP.md`](docs/ROADMAP.md): trabajo completado, en curso y pendiente.

### Infraestructura legacy

Render y Aiven son la infraestructura anterior. Render API y cron están suspendidos; Aiven está fuera del circuito productivo y no debe tratarse como réplica sincronizada. Ver [`docs/MIGRATION_RENDER_AIVEN_TO_OVH.md`](docs/MIGRATION_RENDER_AIVEN_TO_OVH.md).

## Roadmap

- **En curso / pendiente de revalidación:** experiencia completa de lista de espera inteligente en el entorno objetivo.
- **Pendiente:** auditoría de cambios, ampliación de validación PostgreSQL y estabilidad adicional de Playwright E2E.
- **Fuera de alcance:** WhatsApp transaccional, SMS, push, IA, reporting avanzado y directorio público.
- **Ya implementados:** reserva online pública, enlace de adquisición, Centro de Ayuda, analítica PostHog/GA4 e infraestructura OVH.

La fuente de detalle es [`docs/ROADMAP.md`](docs/ROADMAP.md); las prioridades comerciales no están determinadas en el repositorio.

## Licencia

Consultar [`LICENSE`](LICENSE).

## Autor

Mariano Luque Davos · [GitHub](https://github.com/luquemariano)
