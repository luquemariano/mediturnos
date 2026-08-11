# MediTurnos contributor guide

## Project overview

MediTurnos is a full-stack medical appointment management application.

- Backend: FastAPI, SQLAlchemy, Pydantic, Alembic, JWT, and Mercado Pago.
- Frontend: React, TypeScript, Vite, Axios, and plain CSS.
- Production database: PostgreSQL.
- Local/test fallback: SQLite.

## Repository layout

- `app/main.py`: FastAPI application and router registration.
- `app/routers/`: HTTP endpoints and authorization dependencies.
- `app/services/`: business rules and transaction boundaries.
- `app/repositories/`: SQLAlchemy queries and persistence helpers.
- `app/models/`: ORM models.
- `app/schemas/`: Pydantic request and response contracts.
- `app/core/`: settings, authentication, JWT, and authorization.
- `app/database/`: engine and session configuration.
- `app/scripts/seed.py`: idempotent demo data loader.
- `alembic/`: database migrations.
- `frontend/src/`: React application.
- `tests/`: backend tests using an in-memory SQLite database.

## Development commands

Run backend tests:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Run the API locally:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Run the frontend:

```powershell
Set-Location frontend
npm run dev
```

Validate the frontend:

```powershell
Set-Location frontend
npm run lint
npm run build
```

Start the containerized API and PostgreSQL:

```powershell
docker compose --env-file .env up -d --build
```

Do not run migrations or the demo seed unless the task explicitly requires a database change or data setup.

## Implementation conventions

- Keep the existing router-service-repository separation.
- Put HTTP parsing, response models, and permission dependencies in routers.
- Put business validation and transaction handling in services.
- Keep database query details in repositories.
- Represent API inputs and outputs with Pydantic schemas.
- Add an Alembic migration for every persistent schema change; do not rely on `Base.metadata.create_all()` in production.
- Preserve PostgreSQL compatibility even when tests use SQLite.
- Keep user-facing text in Spanish unless the surrounding interface establishes another language.
- Configure deployment-specific URLs, origins, credentials, and secrets through environment variables.
- Never log passwords, JWTs, access tokens, webhook secrets, or patient-sensitive data.

## Authentication and authorization

Supported roles are `administrador`, `recepcionista`, `profesional`, and `paciente`.

- Require authentication by default for application endpoints.
- Apply least-privilege authorization at the router boundary and enforce ownership in the service layer.
- Patients may access only their own profile, appointments, and payments.
- Professionals may access only their own agenda unless an administrative permission explicitly applies.
- Mercado Pago webhooks are public callbacks and must continue validating their signature.

## Scheduling rules

Changes involving appointments must account for:

- active patients, professionals, and services;
- future dates and explicit timezone handling;
- declared professional availability;
- service duration and overlapping appointments;
- valid appointment-state transitions;
- concurrent booking attempts and database-level integrity.

Creation and rescheduling should enforce the same availability rules.

## Testing expectations

- Add or update tests for changed behavior.
- Cover both successful and forbidden role/ownership cases.
- For scheduling changes, test exact collisions, partial overlaps, unavailable hours, cancelled appointments, and concurrent booking behavior where practical.
- For payments, test ownership, duplicate preference handling, and valid/invalid webhook signatures.
- Do not treat SQLite-only tests as proof that Alembic migrations work on PostgreSQL.

## Repository hygiene

- Do not commit `.env`, secrets, local dumps, generated frontend output, caches, or virtual environments.
- Avoid modifying the tracked `mediturnos.db` unless a task explicitly calls for updating that artifact.
- Preserve unrelated user changes in a dirty worktree.
- Do not commit, push, pull, change branches, or run destructive Git commands unless explicitly requested.
