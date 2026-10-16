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

## Fixture sintético de QA del Consultorio

`STAGING_SEED_ENABLED=true` habilita `python3 -m app.scripts.seed_staging` únicamente después de validar `APP_ENV=staging`, `DATABASE_URL` hacia el servicio/base `db/turnelia_staging`, el password de demo y emails `staging-*`. La semilla es idempotente y deja cuatro profesionales activos (administradora clínica, profesional clínico y dos profesionales de estética), con pacientes propios, recurrencias semanales dentro del horizonte de 90 días y turnos futuros sintéticos. La persona `staging-paciente@turnelia.com.ar` se comparte entre las dos profesionales clínicas, con perfiles y evoluciones separados por ownership.

La invitación sintética pendiente anterior se revoca sólo si conserva el email/nombre y la titular sintéticos esperados; se cancelan sus ocurrencias para liberar cupo y sala. Una invitación que no coincide detiene la semilla sin modificarla. Se valida que queden exactamente los cuatro vínculos activos previstos y ninguna invitación pendiente que reserve una quinta plaza. La semilla no imprime contraseñas ni tokens, y no envía correo, WhatsApp ni mensajes. Usar sólo la base desechable de staging o una copia de QA aislada; nunca una base productiva.

Los módulos recurrentes incluyen semanas ocupadas con turnos sintéticos y semanas libres para verificar los bloqueos por turnos y los cambios permitidos. Los datos usan identificadores/correos de staging y textos QA explícitos; no representan personas reales.

### Riesgo de infraestructura Entrega 07

No fue posible inspeccionar el VPS: SSH al IP productivo rechazó la autenticación, y `staging.turnelia.com.ar` aún no resuelve. Por ello no se creó recurso remoto ni se puede afirmar la disponibilidad de puertos, espacio, Caddy, backups o cron. Para continuar, el propietario debe habilitar acceso SSH de solo lectura para la identidad operativa acordada y crear/confirmar el registro DNS staging. Esto no autoriza despliegue ni cambios de producción.
