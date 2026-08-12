<p align="center">
  <img src="docs/images/mediturnos-banner.png" alt="Portada de MediTurnos" width="100%">
</p>

<h1 align="center">MediTurnos</h1>

<p align="center">
  Aplicación Full Stack para la gestión de turnos médicos, desarrollada como proyecto de portfolio.
</p>

<p align="center">
  <strong>FastAPI · React · TypeScript · PostgreSQL · Docker · JWT</strong>
</p>

---

## Descripción

**MediTurnos** es una demostración técnica de una plataforma moderna para consultorios, clínicas y centros de salud. El proyecto integra una API REST con FastAPI, autenticación mediante JWT, persistencia en PostgreSQL, contenedores Docker y una interfaz desarrollada con React y TypeScript.

El alcance fue pensado para portfolio: presenta un recorrido funcional, visualmente atractivo y técnicamente escalable, sin pretender reemplazar un producto médico listo para producción.

## Funcionalidades destacadas

- Inicio de sesión con autenticación JWT.
- Consulta del usuario autenticado y control de acceso por roles.
- Dashboard principal responsive.
- Listado, búsqueda y alta de pacientes.
- Agenda médica agrupada por fecha.
- Filtros por estado y búsqueda de turnos.
- Confirmación y cancelación de turnos.
- Prevención de conflictos de horario.
- Migraciones de base de datos con Alembic.
- Datos demo idempotentes para evaluar el proyecto rápidamente.
- Docker Compose para API y PostgreSQL.

## Tecnologías

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Alembic
- PostgreSQL
- JWT
- pwdlib

### Frontend

- React
- TypeScript
- Vite
- Axios
- CSS responsive

### Infraestructura

- Docker
- Docker Compose
- Git
- GitHub

## Arquitectura

```text
React + TypeScript
        │
        │ Axios + JWT
        ▼
      FastAPI
        │
        ├── Routers
        ├── Services
        ├── Repositories
        ├── Schemas
        └── Models
        │
        ▼
    PostgreSQL
```

## Estructura principal

```text
mediturnos/
├── alembic/
├── app/
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── repositories/
│   ├── routers/
│   ├── schemas/
│   ├── scripts/
│   ├── services/
│   └── main.py
├── frontend/
│   └── src/
│       ├── api/
│       ├── components/
│       ├── services/
│       └── types/
├── docs/
│   └── images/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Ejecución con Docker

### 1. Clonar el repositorio

```bash
git clone https://github.com/luquemariano/mediturnos.git
cd mediturnos
```

### 2. Crear el archivo de variables de entorno

En PowerShell:

```powershell
Copy-Item .env.example .env
```

En Linux o macOS:

```bash
cp .env.example .env
```

Antes de usar el proyecto fuera de una demo local, reemplazá las claves y contraseñas del archivo `.env`.

### 3. Construir y levantar la API y PostgreSQL

```bash
docker compose --env-file .env up -d --build
```

La API quedará disponible en:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

### 4. Cargar datos demo

El seed está deshabilitado por defecto. Antes de ejecutarlo, configurá
explícitamente estas variables en `.env`:

```dotenv
APP_ENV=demo
DEMO_SEED_ENABLED=true
DEMO_ADMIN_EMAIL=tu_admin_demo@ejemplo.com
DEMO_ADMIN_PASSWORD=elegir_una_contraseña_segura
DEMO_ADMIN_RESET_PASSWORD=false
```

`APP_ENV=production` bloquea siempre la ejecución. Si el administrador demo
ya existe, su contraseña sólo se reemplaza cuando
`DEMO_ADMIN_RESET_PASSWORD=true`.

```bash
docker compose --env-file .env exec api python -m app.scripts.seed
```

El script crea o actualiza:

- 1 administrador demo.
- 4 especialidades.
- 5 profesionales.
- 7 prestaciones.
- 8 pacientes demo.
- 15 turnos con diferentes estados.

Puede ejecutarse varias veces sin duplicar los registros principales.

### 5. Ejecutar el frontend

```bash
cd frontend
npm install
npm run dev
```

La aplicación quedará disponible en:

```text
http://localhost:5173
```

## Credenciales demo

El email y la contraseña son los valores que configures en
`DEMO_ADMIN_EMAIL` y `DEMO_ADMIN_PASSWORD`. No hay una contraseña demo
predeterminada. Estas credenciales deben utilizarse únicamente para
desarrollo local o ambientes de demostración.

## Capturas

Guardá las capturas dentro de `docs/images/` con estos nombres y descomentá las líneas correspondientes:

```markdown
<!-- ![Login](docs/images/login.png) -->
<!-- ![Dashboard](docs/images/dashboard.png) -->
<!-- ![Pacientes](docs/images/pacientes.png) -->
<!-- ![Agenda médica](docs/images/agenda.png) -->
```

### Dashboard

<!-- ![Dashboard](docs/images/dashboard.png) -->

### Gestión de pacientes

<!-- ![Pacientes](docs/images/pacientes.png) -->

### Agenda médica

<!-- ![Agenda médica](docs/images/agenda.png) -->

## API

Principales grupos de endpoints:

```text
/auth
/usuarios
/pacientes
/profesionales
/especialidades
/prestaciones
/disponibilidades
/turnos
/pagos
```

La documentación interactiva completa está disponible en `/docs`.

## Decisiones técnicas

- Arquitectura organizada por capas.
- Separación entre routers, servicios y repositorios.
- Validación de entrada y salida con Pydantic.
- Autenticación stateless mediante JWT.
- Carga anticipada de relaciones para evitar consultas N+1 en la agenda.
- Baja dependencia entre frontend y modelos internos del backend.
- Script demo idempotente para mejorar la experiencia de evaluación.

## Alcance y evolución futura

MediTurnos es una demo técnica escalable. Algunas extensiones posibles:

- Calendario semanal y mensual.
- CRUD completo de profesionales y especialidades.
- Recordatorios por correo o WhatsApp.
- Recuperación de contraseña.
- Auditoría de cambios.
- Pruebas automatizadas adicionales.
- Despliegue en la nube.
- Integración productiva de pagos y notificaciones.

## Estado del proyecto

**Versión de portfolio funcional.**

El proyecto demuestra el ciclo completo de una aplicación Full Stack: autenticación, API REST, reglas de negocio, persistencia, frontend, contenedores, datos demo y documentación.

## Autor

**Mariano Luque Davos**

- GitHub: `luquemariano`
- Córdoba, Argentina
