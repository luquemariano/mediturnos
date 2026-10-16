# Arquitectura de Turnelia

Estado: **ACTUAL**, basado en el repositorio inspeccionado el 2026-10-15.

```text
Browser → React + TypeScript + Axios + JWT
       → FastAPI → routers → services → repositories → SQLAlchemy
       → PostgreSQL productivo / SQLite principalmente en tests
```

## Backend

`app/main.py` crea FastAPI y registra routers. `app/core/` concentra configuración, JWT, dependencias, fecha/hora y rate limiting. `app/schemas/` define contratos Pydantic; `app/models/` define ORM; `app/repositories/` encapsula consultas; `app/services/` contiene reglas de negocio y transacciones.

Flujo típico: `HTTP → router → Depends(auth/rol/db) → service → repository/ORM → commit → schema/respuesta`. Algunas verificaciones de rol y ownership permanecen en routers.

## Frontend

`frontend/src/main.tsx` monta `App.tsx`. El routing actual es manual mediante `window.location.pathname`, `history.pushState` y `popstate`; no se encontró React Router. `frontend/src/services/` y `frontend/src/api/` realizan llamadas Axios mediante `VITE_API_URL`.

El JWT se conserva en `localStorage` como `access_token`; una respuesta `401` provoca cierre de sesión mediante un evento global.

## Datos y seguridad

SQLAlchemy usa PostgreSQL con `psycopg`; PostgreSQL es el motor configurado/declarado para producción. PostgreSQL de producción: Aiven, según la configuración/historia operativa documentada. El estado operativo actual no fue verificado en esta fase. SQLite aparece principalmente en tests. Alembic mantiene el esquema; la revisión base integrada es `c04inv202610` (invitaciones y destinos pendientes de módulos); Entrega 06 agrega `a7b8c9d0e1f2` para actividad profesional y matrícula condicional. La API usa Bearer JWT y roles `administrador`, `recepcionista`, `profesional` y `paciente`, con ownership adicional.

Las Entregas 01–04 están integradas en `main`. La Entrega 04 agrega `InvitacionConsultorio` y permite que series/ocurrencias apunten a profesional o invitación, con un check XOR. Una ocurrencia pendiente queda activa y participa de la misma exclusión GiST de sala; carece de `profesional_id` y no valida ni permite turnos. La aceptación bloquea primero la fila del consultorio para serializar cupos, exige usuario profesional autenticado con email verificado coincidente y, en una transacción, crea/activa `ConsultorioProfesional` y reasigna series/ocurrencias al perfil existente. El hash del token se conserva tras aceptar para permitir reintentos idempotentes del mismo usuario; revocación/vencimiento lo invalidan. El enlace usa el fragmento del navegador (no se envía en la petición HTTP), y el frontend conserva el token sólo en memoria. Para cuenta nueva se abre el registro individual en otra pestaña; no se almacena un handoff en servidor. La Entrega 06 agrega el catálogo `ActividadProfesional`; alta, onboarding y edición consultan sus requisitos en backend. Las actividades matriculables requieren matrícula y especialidad, mientras que estética asocia en backend la categoría de prestación “Estética” sin solicitar matrícula ni especialidad al usuario. No se crea perfil clínico ni se transfiere `Profesional.cuenta_id`; la administración no habilita rutas clínicas ajenas.

La Entrega 05 añade el panel `/app/consultorio` dentro de la sesión y el shell profesional existentes. El acceso de navegación se muestra después de consultar `GET /consultorios`; la ruta y todas las lecturas/mutaciones siguen verificadas por backend mediante `ConsultorioAdministrador`. `GET /{id}/profesionales` y `GET /{id}/reglas-modulo` aportan DTOs de lista permitida para formularios; la agenda usa la API administrativa de ocurrencias. La agenda semanal presenta sala, horario, estado y profesional asignado o la etiqueta genérica “Invitación pendiente”. La UI consume las APIs existentes para recurrencias, módulos puntuales, cambios, suspensiones e invitaciones. No se añadieron tablas ni migraciones. La Entrega 06 añade el catálogo `actividades_profesionales`, asociado opcionalmente a `Profesional`; alta, onboarding y edición resuelven requisitos en el servicio desde este catálogo, no desde el rol ni flags del cliente. La actividad de estética enlaza a la categoría de prestaciones “Estética”. Actividad nula preserva perfiles previos sin clasificación automática.

## Integraciones y workers

- Mercado Pago: pagos clínicos y suscripciones SaaS, ambos implementados en código con flujos separados; operación real NO DETERMINADA.
- Resend: proveedor de emails implementado/configurable; uso productivo real NO DETERMINADO.
- Cloudflare R2: integración implementada/configurable; también existe implementación fake; uso real NO DETERMINADO.
- Render Cron: `python -m app.scripts.process_appointment_reminders`, DECLARADO EN CONFIGURACIÓN cada 15 minutos; ejecución real NO DETERMINADA.

## Deployment lógico

`render.yaml` declara Web Service Docker para API, Static Site para frontend y Cron Job. `Dockerfile` usa Python 3.14-slim y `app.scripts.start`; el arranque ejecuta `alembic upgrade head` antes de Uvicorn. La operación efectiva de Render es **NO DETERMINADA** sólo por el repositorio.

## Límites actuales

- No hay router dedicado en frontend.
- SQLite en tests no equivale automáticamente a PostgreSQL.
- Disponibilidad real de servicios externos y producción: **NO DETERMINADA**.
- La cuenta organizacional debe existir y tener propietaria verificada para crear un Consultorio; la Entrega 05 no crea cuentas, membresías ni perfiles profesionales.
- Entrega 05 está integrada en `main`; el estado de despliegue de Consultorio no se infiere de este checkout. La Entrega 06 está en implementación en la rama `codex/consultorio-06-actividad-matricula`; su migración es aditiva y el downgrade se protege cuando existan perfiles clasificados o matrículas nulas.

## Preproducción aislada (Entrega 07, en preparación; no desplegada)

`docker-compose.staging.yml` define un proyecto distinto (`turnelia-staging`) con PostgreSQL 18, API y Nginx, volúmenes y redes propias. DB permanece sin puerto publicado en red interna; frontend/API sólo publican en `127.0.0.1:18080/18081`. El Nginx de staging añade `noindex` y `robots.txt` con `Disallow: /`; el build omite analítica. Configuración sensible vive fuera del repositorio (`STAGING_ENV_FILE`). El API valida `APP_ENV=staging`, DB esperada, sandbox de pagos y proveedores de correo/WhatsApp permitidos.

`python -m app.scripts.seed_staging` requiere `STAGING_SEED_ENABLED=true` y sólo admite la base `turnelia_staging` en host `db`; genera identidades sintéticas `staging-*@turnelia.com.ar`, aceptadas por el schema de login, y datos ficticios. El modo `--actualizar-emails-sinteticos` renombra de forma idempotente identidades legacy `example.invalid` tras verificar marcadores de staging, sin cambiar contraseñas ni datos clínicos. Migraciones se ejecutan explícitamente con `alembic upgrade head` en ese servicio. `scripts/staging/manage.sh` valida topología antes de operar; `remove` además inspecciona etiquetas de propiedad antes de retirar recursos. `scripts/staging/backup_restore_check.sh` prueba dump, checksum y restore temporal exclusivamente dentro de staging. No integra `proxy`/Caddy ni accede a backups productivos.
