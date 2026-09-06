# Deployment de Turnelia

Estado: **VERIFICADO EN PRODUCCIÓN** desde el cutover del **2026-09-05 / 2026-09-06 UTC**.

La historia completa del cambio de infraestructura está en `docs/MIGRATION_RENDER_AIVEN_TO_OVH.md`.

## Arquitectura productiva actual

Turnelia se ejecuta en un VPS OVH con Ubuntu 24.04:

- Frontend React/Vite servido por Nginx en Docker.
- Backend FastAPI en Docker.
- PostgreSQL 18 en Docker.
- Caddy como reverse proxy y terminación TLS.
- Recordatorios ejecutados por cron del host cada 15 minutos.
- Backups PostgreSQL diarios mediante `pg_dump` + SHA256.
- Cloudflare como DNS autoritativo.
- Resend para email productivo.
- Mercado Pago para suscripciones SaaS.

Directorio del deployment:

```text
/srv/apps/turnelia
```

Archivos principales:

```text
/srv/apps/turnelia/docker-compose.vps.yml
/srv/apps/turnelia/.env.vps
/srv/apps/proxy/Caddyfile
```

Contenedores esperados:

```text
turnelia-ovh-api
turnelia-ovh-db
turnelia-ovh-frontend
caddy
```

## Dominios

Producción:

```text
https://turnelia.com.ar
https://www.turnelia.com.ar
https://api.turnelia.com.ar
```

`www.turnelia.com.ar` redirige a `https://turnelia.com.ar`.

Accesos técnicos mantenidos temporalmente:

```text
https://ovh.turnelia.com.ar
https://api-ovh.turnelia.com.ar
```

Todos los dominios anteriores han sido comprobados por HTTPS después del cutover.

## PostgreSQL

Producción usa PostgreSQL dentro del stack Docker del VPS.

La API resuelve el servicio PostgreSQL mediante la red interna de Docker (`db:5432`). No depende de Aiven.

Aiven fue el proveedor productivo anterior y permanece temporalmente como infraestructura legacy/contingencia, sin tráfico productivo.

No almacenar `DATABASE_URL` real ni credenciales en Git.

## Caddy

Bloques productivos relevantes:

```caddyfile
turnelia.com.ar {
    reverse_proxy turnelia-ovh-frontend:80
}

www.turnelia.com.ar {
    redir https://turnelia.com.ar{uri} permanent
}

api.turnelia.com.ar {
    reverse_proxy turnelia-ovh-api:8000
}
```

Caddy obtiene y renueva automáticamente los certificados HTTPS.

## Variables de entorno

Producción utiliza:

```text
/srv/apps/turnelia/.env.vps
```

La plantilla versionada es:

```text
.env.vps.example
```

Variables clave de infraestructura:

```text
APP_ENV
DATABASE_URL
FRONTEND_URL
PUBLIC_API_URL
CORS_ALLOWED_ORIGINS
EMAIL_PROVIDER
RESEND_API_KEY
EMAIL_FROM
MERCADOPAGO_ENV
MERCADOPAGO_ACCESS_TOKEN
MERCADOPAGO_PUBLIC_KEY
MERCADOPAGO_WEBHOOK_SECRET
VITE_API_URL
VITE_MERCADOPAGO_PUBLIC_KEY
```

No se versionan valores productivos reales.

## Email / Resend

Configuración productiva verificada:

```text
EMAIL_PROVIDER=resend
EMAIL_FROM=Turnelia <no-reply@mail.turnelia.com.ar>
```

Se probó en producción el flujo de recuperación de contraseña, incluyendo entrega real del email, remitente correcto, URL productiva y restablecimiento final.

## Mercado Pago

Suscripciones SaaS usan la familia `MERCADOPAGO_*`.

Producción fue verificada mediante una asociación real de medio de pago. La suscripción aceptada quedó con proveedor `mercadopago`, estado de cuenta `trial` y `mp_status=authorized`.

Los planes productivos configurados son:

- Profesional: ARS 34.900/mes.
- Consultorio: ARS 69.900/mes.
- Centro: ARS 149.900/mes.

Cada plan mantiene su `mp_preapproval_plan_id` productivo.

## Recordatorios

Render Cron fue reemplazado por cron del host.

Configuración productiva:

```cron
*/15 * * * * cd /srv/apps/turnelia && /usr/bin/docker compose --env-file .env.vps -f docker-compose.vps.yml --profile reminders run --rm reminders >> /var/log/turnelia-reminders.log 2>&1
```

El comando ejecuta una pasada de:

```text
python -m app.scripts.process_appointment_reminders
```

y finaliza.

## Backups

Script del host:

```text
/usr/local/bin/backup-turnelia.sh
```

Destino:

```text
/srv/apps/turnelia/backups/automatic
```

Programación:

```cron
30 3 * * * /usr/local/bin/backup-turnelia.sh >> /var/log/backup-turnelia.log 2>&1
```

Política actual:

- dump PostgreSQL custom format;
- archivo SHA256 asociado;
- retención local de 14 días;
- ejecución diaria.

## Salud operativa

Health público:

```bash
curl -s https://api.turnelia.com.ar/health/ready
```

Esperado:

```json
{"status":"ok"}
```

Diagnóstico completo del VPS:

```bash
health
```

El alias apunta a:

```text
/usr/local/bin/health-vps.sh
```

El health check revisa recursos, Docker, contenedores, Turnelia, Orienta, cron, reminders, backups, checksums, UFW, Fail2ban y errores recientes.

## Deploy seguro

Antes de cualquier cambio:

```bash
cd /srv/apps/turnelia
python3 scripts/check_env_duplicates.py .env.vps
docker compose --env-file .env.vps -f docker-compose.vps.yml config
```

Backend:

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml build api
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d api
```

Frontend:

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml build frontend
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d frontend
```

Evitar recrear servicios que no cambiaron.

## Regla crítica de datos

No ejecutar:

```bash
docker compose down -v
```

porque elimina volúmenes persistentes.

Antes de cambios destructivos de base, generar un dump verificable.

## Legacy y rollback

Render API y Render Cron están suspendidos. Aiven está fuera del circuito productivo.

Después de que OVH comenzó a aceptar nuevas escrituras, volver simplemente a Render + Aiven dejó de ser un rollback seguro. Cualquier recuperación posterior al cutover debe preservar o sincronizar primero los datos nuevos de PostgreSQL OVH.

Consultar `docs/MIGRATION_RENDER_AIVEN_TO_OVH.md` para el procedimiento y las evidencias del cutover.
