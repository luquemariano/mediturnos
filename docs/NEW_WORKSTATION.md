# Nueva estación de trabajo

Guía para preparar Turnelia en una desktop, notebook o PC nueva sin copiar secretos de producción.

## Principio

Hay tres capas separadas:

```text
GitHub
├── código
├── .env.example
└── .env.vps.example

PC de desarrollo
└── .env

OVH producción
└── /srv/apps/turnelia/.env.vps
```

GitHub versiona contratos y plantillas. La PC mantiene sólo su configuración local. El VPS mantiene la configuración productiva real.

## 1. Clonar el repositorio

```powershell
git clone https://github.com/luquemariano/mediturnos.git
cd mediturnos
```

Verificar:

```powershell
git status
git branch --show-current
```

La rama inicial debe ser `main` y el working tree debe estar limpio.

## 2. Crear el entorno local

En Windows/PowerShell:

```powershell
Copy-Item .env.example .env
```

En Linux/macOS:

```bash
cp .env.example .env
```

Completar únicamente los valores necesarios para desarrollo local.

El entorno local debe conservar, salvo una necesidad explícita diferente:

```text
APP_ENV=development
FRONTEND_URL=http://localhost:5173
PUBLIC_API_URL=http://localhost:8000
EMAIL_PROVIDER=in_memory
MERCADOPAGO_ENV=sandbox
```

No copiar `.env.vps` desde producción para desarrollar.

## 3. Secretos locales

`.env` no se versiona.

Cada estación puede tener sus propios valores de desarrollo, por ejemplo:

- contraseña de PostgreSQL local;
- JWT de desarrollo;
- secretos de acciones de turnos/estudios;
- credenciales sandbox de Mercado Pago si se prueban pagos;
- claves de servicios externos sólo cuando una prueba local las requiera.

Para desarrollo normal, preferir proveedores locales/fake/in-memory cuando el proyecto ya los soporte.

## 4. Producción

La configuración real de producción vive exclusivamente en:

```text
/srv/apps/turnelia/.env.vps
```

El contrato de variables productivas está versionado en:

```text
.env.vps.example
```

`.env.vps.example` describe nombres y valores no secretos de producción, pero no contiene credenciales reales.

Para revisar o modificar producción, conectarse al VPS y trabajar allí:

```powershell
ssh root@66.70.190.84
```

Luego:

```bash
cd /srv/apps/turnelia
```

No es necesario tener `.env.vps` en la desktop o notebook para hacer desarrollo cotidiano.

## 5. Antes de empezar a trabajar

```powershell
git switch main
git pull --ff-only
git status
```

Crear luego una rama de trabajo:

```powershell
git switch -c feature/nombre-cambio
```

No desarrollar directamente sobre `main`.

## 6. Si se cambia de PC

La nueva máquina necesita:

1. acceso a GitHub;
2. Git;
3. runtime y herramientas requeridas por el proyecto;
4. clon del repositorio;
5. `.env` local creado desde `.env.example`;
6. credenciales sandbox/locales necesarias para la tarea.

No necesita:

- copia de `.env.vps`;
- copia de la base productiva;
- credenciales productivas para cambios que no requieran tocar producción.

## 7. Si se pierde una PC

Producción no se ve afectada porque:

- el código está en GitHub;
- la base productiva vive en el VPS;
- `.env.vps` vive en el VPS;
- los backups productivos se generan en el VPS.

La estación se reconstruye clonando el repo y recreando `.env` desde `.env.example`.

## 8. Si se pierde el VPS

La reconstrucción requiere:

- repositorio GitHub;
- `.env.vps.example` como contrato;
- backup reciente de PostgreSQL;
- copia segura externa de los secretos productivos;
- configuración de DNS/Cloudflare/Caddy documentada;
- runbook de `docs/OPERATIONS_VPS.md`;
- historia de `docs/MIGRATION_RENDER_AIVEN_TO_OVH.md`.

Por eso los secretos productivos deben contar con una copia de recuperación externa al VPS, almacenada de forma segura, pero nunca dentro del repositorio.

## 9. Archivos que nunca deben entrar al repositorio

```text
.env
.env.vps
.env.local
.env.*.local
```

Las plantillas que sí se versionan son:

```text
.env.example
.env.vps.example
```

## 10. Checklist rápido

- [ ] repo clonado;
- [ ] `main` actualizado;
- [ ] `.env` creado desde `.env.example`;
- [ ] variables locales completas;
- [ ] no existe `.env.vps` en la estación salvo necesidad operativa excepcional;
- [ ] `git status` no muestra archivos de secretos;
- [ ] rama de trabajo creada antes de modificar código.
