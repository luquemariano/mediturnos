<p align="center">
  <img src="frontend/public/brand/mediturnos-logo-horizontal.svg" alt="Turnelia" width="320">
</p>

<h1 align="center">Turnelia</h1>

<p align="center">
  Aplicación Full Stack para la gestión de turnos médicos, desarrollada como proyecto de portfolio.
</p>

<p align="center">
  <strong>FastAPI · React · TypeScript · PostgreSQL · Docker · JWT</strong>
</p>

---

## Descripción

**Turnelia** es una demostración técnica de una plataforma moderna para consultorios, clínicas y centros de salud. El repositorio conserva internamente el nombre `mediturnos`. El proyecto integra una API REST con FastAPI, autenticación mediante JWT, persistencia en PostgreSQL, contenedores Docker y una interfaz desarrollada con React y TypeScript.

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

El contenedor aplica `alembic upgrade head` antes de iniciar Uvicorn. El
puerto se controla con `PORT` y usa `8000` si no se configura. En
`APP_ENV=production`, la API valida la configuración de PostgreSQL, JWT y
CORS, y deshabilita `/docs`, `/redoc` y `/openapi.json`. Los endpoints
`/health/live` y `/health/ready` quedan disponibles para monitoreo.

Para crear manualmente el primer administrador de una instalación vacía,
configurá `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD` y,
opcionalmente, `BOOTSTRAP_ADMIN_NAME`. Luego ejecutá:

```bash
docker compose --env-file .env exec api python -m app.scripts.bootstrap_admin
```

Este comando no se ejecuta durante el arranque y se bloquea si ya existe un
administrador o si el email pertenece a otra cuenta.

### Email de recuperación de contraseña

En `development`, `demo` y `test`, usá el proveedor local para evitar cualquier
dependencia de Internet:

```dotenv
EMAIL_PROVIDER=in_memory
FRONTEND_URL=http://localhost:5173
PASSWORD_RESET_EXPIRE_MINUTES=60
```

Los enlaces se conservan únicamente en una salida controlada en memoria. En
estos entornos no necesitás comprar ni verificar un dominio.

En producción, `FRONTEND_URL` debe ser la URL pública donde está desplegado el
frontend. Puede ser un subdominio asignado por el hosting —por ejemplo,
`https://mi-app.onrender.com`— y no necesita coincidir con el dominio remitente
del correo. Turnelia exige además un proveedor transaccional real:

```dotenv
EMAIL_PROVIDER=resend
RESEND_API_KEY=configurar_como_secreto
EMAIL_FROM=Turnelia <no-reply@dominio-verificado.example>
FRONTEND_URL=https://url-publica-asignada-por-el-hosting.example
```

`FRONTEND_URL` no requiere un dominio comprado: puede cambiarse por la URL
provista por Render u otro hosting. En cambio, para enviar correos reales a
destinatarios externos, Resend exige verificar un dominio propio con acceso a
sus registros DNS. `EMAIL_FROM` debe pertenecer a ese dominio verificado.
La API key debe gestionarse como secreto y nunca incluirse en el repositorio
ni en logs. `FRONTEND_URL` debe ser pública y no puede apuntar a localhost en
producción.

Resend ofrece `onboarding@resend.dev` para pruebas limitadas: sólo permite
enviar al email asociado a la propia cuenta de Resend. También ofrece
destinatarios especiales `@resend.dev` para simular entrega, rebote o denuncia.
Estas opciones sirven para verificar la integración antes de comprar un
dominio, pero no permiten recuperación real para usuarios externos y no deben
usarse como configuración productiva.

Cuando exista un dominio propio, no será necesario modificar `auth_service` ni
la lógica de recuperación. Bastará con verificar el dominio en Resend y cambiar
`EMAIL_FROM` y `FRONTEND_URL` en el entorno del deployment.

Si Resend rechaza o no puede entregar la solicitud, la operación de base se
revierte y el nuevo token no queda utilizable. La respuesta pública continúa
siendo genérica para no revelar si el email pertenece a una cuenta.

### Deploy en Render

El repositorio incluye `render.yaml` para crear mediante un Blueprint tres
recursos conectados: PostgreSQL administrado, la API FastAPI como Web Service
Docker y el frontend React como Static Site. El Blueprint no contiene secretos.
Al importar el Blueprint, seleccioná la rama que quieras desplegar; para esta
primera prueba corresponde `feature/mvp`. Como no se declara `repo` ni `branch`
en el archivo, Render utiliza el repositorio y la rama vinculados al Blueprint.

Para una URL pública se recomienda `APP_ENV=production`, aunque el despliegue
sea de prueba. De este modo siguen vigentes las garantías de producción: no se
admite SQLite, el secreto JWT debe ser fuerte, Swagger/OpenAPI queda
deshabilitado, CORS no acepta `*` ni localhost, el seed demo queda bloqueado y
la recuperación requiere un proveedor real. Usar `APP_ENV=demo` expondría
herramientas y datos pensados para un entorno controlado y no es la opción
recomendada para un servicio accesible desde Internet.

Al crear el Blueprint, Render solicita los valores marcados con `sync: false`.
Configurá en el backend:

| Variable | Requerida | Configuración |
| --- | --- | --- |
| `APP_ENV` | Sí | Definida como `production` por el Blueprint. |
| `DATABASE_URL` | Sí | Inyectada desde el PostgreSQL administrado; no cargarla manualmente. |
| `APP_TIMEZONE` | Sí | Definida como `America/Argentina/Buenos_Aires`. |
| `JWT_SECRET_KEY` | Sí | Generada de forma segura por Render. |
| `JWT_ALGORITHM` | Sí | Definida como `HS256`. |
| `JWT_EXPIRE_MINUTES` | Sí | Definida como `60`; puede ajustarse. |
| `CORS_ALLOWED_ORIGINS` | Sí | Definida con los dominios públicos de Turnelia y, temporalmente, el Static Site de Render. |
| `FRONTEND_URL` | Sí | Definida como `https://turnelia.com.ar`. |
| `PASSWORD_RESET_EXPIRE_MINUTES` | Sí | Definida como `60`; puede ajustarse. |
| `EMAIL_PROVIDER` | Sí | Definida como `resend`. |
| `RESEND_API_KEY` | Sí | Secreto cargado desde el Dashboard de Render. |
| `EMAIL_FROM` | Sí | Remitente autorizado por Resend. |
| `MERCADO_PAGO_ACCESS_TOKEN` | No | Sólo cuando se habiliten pagos reales. |
| `MERCADO_PAGO_WEBHOOK_SECRET` | No | Sólo cuando se habiliten webhooks reales. |

En el frontend, `VITE_API_URL` es obligatoria durante el build y está definida
como `https://api.turnelia.com.ar`. Vite incorpora este valor al bundle: si
cambia la URL de la API, hay que reconstruir el Static Site.

Las variables `DEMO_SEED_ENABLED`, `DEMO_ADMIN_*` y
`DEMO_PROFESSIONAL_*` no se configuran en este despliegue porque el seed está
bloqueado en `production`. Tampoco se deben cargar `.env` ni secretos en Git.

El Web Service usa el `Dockerfile` de la raíz. Su comando de inicio es
`python -m app.scripts.start`: primero ejecuta `alembic upgrade head` y sólo si
la migración termina correctamente inicia Uvicorn en `0.0.0.0:$PORT`. Render
inyecta `PORT`; Docker Compose local conserva su valor predeterminado `8000`.
La URL de PostgreSQL entregada como `postgresql://` se normaliza internamente a
`postgresql+psycopg://`.

El Static Site usa:

```text
Root Directory: frontend
Build Command: npm ci && npm run build
Publish Directory: dist
```

La regla `/* -> /index.html` incluida en el Blueprint permite abrir directamente
rutas del cliente como `/reset-password?token=...` sin recibir un 404.

Render debe comprobar la API mediante `GET /health/ready`, que valida tanto el
proceso como la conexión a PostgreSQL. `GET /health/live` queda disponible como
sonda de vida sin acceso a la base.

Inicialmente pueden utilizarse las URLs asignadas por Render:

```text
Frontend: https://<frontend>.onrender.com
Backend:  https://<backend>.onrender.com
```

Configurá `FRONTEND_URL` y el único origen de `CORS_ALLOWED_ORIGINS` con la
primera URL, y `VITE_API_URL` con la segunda. Esto no elimina la restricción del
remitente: para enviar emails a usuarios externos, Resend requiere un dominio
verificado. Su remitente de prueba sólo sirve bajo las limitaciones documentadas
en la sección anterior.

Los Custom Domains activos son `turnelia.com.ar` para el Static Site y
`api.turnelia.com.ar` para el Web Service. La configuración productiva es:

```text
FRONTEND_URL=https://turnelia.com.ar
CORS_ALLOWED_ORIGINS=["https://turnelia.com.ar","https://www.turnelia.com.ar","https://mediturnos-frontend-711v.onrender.com"]
VITE_API_URL=https://api.turnelia.com.ar
```

El origen `https://mediturnos-frontend-711v.onrender.com` se conserva
temporalmente para que el frontend técnico de Render siga pudiendo llamar a la
API. La URL `https://mediturnos-api-14d3.onrender.com` también puede permanecer
activa como alias del backend, pero no debe usarse como `VITE_API_URL`: CORS
valida el origen del frontend, no la URL del backend. Cuando se decida retirar
el acceso por la URL técnica del frontend, se puede quitar únicamente ese
origen de `CORS_ALLOWED_ORIGINS`.

El cambio de dominio no requiere modificar la aplicación. Render administra el
certificado TLS; el Static Site debe reconstruirse porque Vite incorpora
`VITE_API_URL` durante el build. En servicios de Render ya creados, verificá
manualmente los tres valores anteriores en **Environment** y desplegá de nuevo
el backend y el frontend. Si se usa el dominio para enviar emails, también debe
verificarse en Resend y actualizarse `EMAIL_FROM` desde el entorno.

El plan gratuito es sólo para esta prueba: el Web Service puede suspenderse por
inactividad y tener un arranque lento. PostgreSQL gratuito está limitado a 1 GB,
no ofrece backups y expira 30 días después de su creación; tras el período de
gracia, Render elimina la base. No debe utilizarse para clientes pagos ni para
información real que necesite persistencia, recuperación o garantías operativas.
Antes de una prueba prolongada o comercial, migrá a una base paga con backups y
revisá los planes vigentes de Render.

### 4. Cargar datos demo

El seed está deshabilitado por defecto. Antes de ejecutarlo, configurá
explícitamente estas variables en `.env`:

```dotenv
APP_ENV=demo
DEMO_SEED_ENABLED=true
DEMO_ADMIN_EMAIL=admin.demo@mediturnos.com.ar
DEMO_ADMIN_PASSWORD=elegir_una_contraseña_segura
DEMO_ADMIN_RESET_PASSWORD=false
DEMO_PROFESSIONAL_EMAIL=profesional.demo@mediturnos.com.ar
DEMO_PROFESSIONAL_PASSWORD=elegir_otra_contraseña_segura
DEMO_PROFESSIONAL_RESET_PASSWORD=false
```

`APP_ENV=production` bloquea siempre la ejecución. Si el administrador demo
ya existe, su contraseña sólo se reemplaza cuando
`DEMO_ADMIN_RESET_PASSWORD=true`.
La cuenta profesional queda vinculada al perfil demo con matrícula
`MP-DEMO-PSIQ-001`. Su contraseña tampoco se reemplaza salvo que
`DEMO_PROFESSIONAL_RESET_PASSWORD=true`.

```bash
docker compose --env-file .env exec api python -m app.scripts.seed
```

El script crea o actualiza:

- 1 administrador demo y 1 usuario profesional demo.
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

Turnelia es una demo técnica escalable. Algunas extensiones posibles:

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
