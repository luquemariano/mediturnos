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

SQLAlchemy usa PostgreSQL con `psycopg`; PostgreSQL es el motor configurado/declarado para producción. PostgreSQL de producción: Aiven, según la configuración/historia operativa documentada. El estado operativo actual no fue verificado en esta fase. SQLite aparece principalmente en tests. Alembic mantiene el esquema; la revisión actual de esta rama es `c04inv202610` (invitaciones y destinos pendientes de módulos). La API usa Bearer JWT y roles `administrador`, `recepcionista`, `profesional` y `paciente`, con ownership adicional.

La fundación y la Entrega 03 están integradas en `main`. La Entrega 04 agrega `InvitacionConsultorio` y permite que series/ocurrencias apunten a profesional o invitación, con un check XOR. Una ocurrencia pendiente queda activa y participa de la misma exclusión GiST de sala; carece de `profesional_id` y no valida ni permite turnos. La aceptación bloquea primero la fila del consultorio para serializar cupos, exige usuario profesional autenticado con email verificado coincidente y, en una transacción, crea/activa `ConsultorioProfesional` y reasigna series/ocurrencias al perfil existente. El hash del token se conserva tras aceptar para permitir reintentos idempotentes del mismo usuario; revocación/vencimiento lo invalidan. El enlace usa el fragmento del navegador (no se envía en la petición HTTP), y el frontend conserva el token sólo en memoria. Para cuenta nueva se abre el registro individual en otra pestaña; no se almacena un handoff en servidor. El formulario actual exige matrícula y especialidad, por lo que actividades sin esos requisitos siguen bloqueadas por el alta existente. No se crea perfil clínico ni se transfiere `Profesional.cuenta_id`; la administración no habilita rutas clínicas ajenas.

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
- La cuenta organizacional debe existir y tener propietaria verificada para crear un Consultorio; esta entrega no crea cuentas, membresías, invitaciones ni perfiles profesionales.
