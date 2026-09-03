# Despliegue paralelo en VPS OVH

Estado: configuración preparada; operación externa y DNS son **NO DETERMINADOS**.

Este stack es independiente de Render. No modifica `render.yaml`, los dominios productivos ni el Compose de desarrollo.

## Arquitectura

`frontend` (Nginx) queda disponible para Caddy como `http://frontend:80` en la red externa Docker `proxy`. `api` queda disponible como `http://api:8000` en esa misma red. Caddy debe asociar esos upstreams a `ovh.turnelia.com.ar` y `api-ovh.turnelia.com.ar`.

PostgreSQL sólo está en `turnelia_internal`, una red marcada como `internal`; API y el worker acceden a ella por el nombre `db`. Ningún servicio publica puertos al host.

Servicios: `db`, `api`, `frontend` y `reminders`. El worker tiene el perfil `reminders` y no se inicia con el deploy normal.

## Preparación

```bash
cp .env.vps.example .env.vps
# Completar .env.vps en el VPS; no versionarlo
docker network inspect proxy >/dev/null
docker compose --env-file .env.vps -f docker-compose.vps.yml config
```

El archivo debe contener secretos generados específicamente para staging. `JWT_SECRET_KEY`, `APPOINTMENT_ACTION_SECRET` y `STUDY_ACCESS_SECRET` deben ser aleatorios; los dos últimos necesitan al menos 32 caracteres.

## Frontend y variables

El build usa Node 24 Alpine, `npm ci` y Vite. `VITE_API_URL` y `VITE_MERCADOPAGO_PUBLIC_KEY` se consumen durante el build, por lo que cambiar cualquiera de ellas requiere reconstruir la imagen `frontend`. Nginx conserva las rutas SPA con `try_files ... /index.html` y aplica cache a assets versionados.

## Deploy y migraciones

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml build
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d db api frontend
docker compose --env-file .env.vps -f docker-compose.vps.yml ps
```

La API conserva el `CMD` del Dockerfile y `app.scripts.start` ejecuta `alembic upgrade head` antes de Uvicorn. No ejecutar migraciones manuales en paralelo contra una base compartida con Render. En esta primera etapa la base de OVH es independiente.

Los healthchecks son `pg_isready` para PostgreSQL y `/health/ready` para API; este último valida PostgreSQL. Verificar desde Caddy las dos URLs HTTPS previstas antes de considerar listo el staging.

## Recordatorios

No iniciar el perfil `reminders` durante pruebas de staging. Cuando exista una base y un proveedor de email de staging confirmados, usar cron del host cada 15 minutos:

```cron
*/15 * * * * cd /ruta/turnelia && docker compose --env-file .env.vps -f docker-compose.vps.yml --profile reminders run --rm reminders
```

El comando es de ejecución puntual y no contiene un loop `sleep`. Antes de habilitarlo, confirmar que `DATABASE_URL` apunta a la base OVH y que los emails no salen a pacientes reales.

## Pagos y seguridad operacional

Mantener `MERCADOPAGO_ENV=sandbox`, usar usuarios de prueba y revisar webhooks antes de cualquier prueba. No copiar tokens productivos a `.env.vps`. Recordatorios y Resend deben permanecer desactivados, apuntar a destinatarios controlados o usar un proveedor/configuración de staging hasta contar con confirmación explícita.

## Rollback

Para volver a la imagen anterior, conservar el tag o digest desplegado y ejecutar `docker compose ... up -d` con esa referencia. Para detener sólo OVH: `docker compose ... stop api frontend` (la base se conserva). No borrar el volumen sin un backup verificado.

## Migración futura desde Render

La migración de base debe planificarse como operación separada: backup probado, ventana de escritura, compatibilidad de migraciones Alembic, restauración en una base OVH aislada, validación de healthchecks y datos, y cambio de DNS/proxy sólo después de verificar. No existe actualmente una sincronización o replicación declarada entre Render/Aiven y OVH.
