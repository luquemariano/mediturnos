# Migración productiva de Turnelia: Render/Aiven → OVH VPS

Fecha de cutover: **2026-09-05 / 2026-09-06 UTC**  
Estado: **COMPLETADA Y VERIFICADA EN PRODUCCIÓN**

Este documento registra la migración de Turnelia desde Render + Aiven hacia un VPS propio en OVH. El objetivo es que el procedimiento, decisiones, validaciones, contingencias y estado final puedan reconstruirse en el futuro sin depender del historial de una terminal o de conversaciones externas.

> Este documento no contiene contraseñas, tokens, access tokens, secretos de webhooks ni connection strings completos. Los secretos productivos viven fuera del repositorio.

## 1. Arquitectura anterior

Antes del cutover productivo, Turnelia operaba con:

- Frontend React/Vite: Render Static Site.
- Backend FastAPI: Render Web Service.
- Recordatorios: Render Cron Job cada 15 minutos.
- PostgreSQL: Aiven.
- DNS: Cloudflare.
- Email: Resend.
- Suscripciones: Mercado Pago.

Servicios históricos de Render:

- Frontend: `mediturnos-frontend-711v.onrender.com`
- API: `mediturnos-api-14d3.onrender.com`
- Cron: `turnelia-appointment-reminders`

Base histórica Aiven:

- PostgreSQL 18.6.
- Base productiva migrada mediante `pg_dump` custom format y `pg_restore`.

## 2. Arquitectura productiva final

Producción quedó consolidada en un VPS OVH:

- Ubuntu 24.04.
- Docker Engine + Docker Compose.
- Caddy como reverse proxy y terminación HTTPS.
- PostgreSQL 18 en contenedor Docker.
- FastAPI en contenedor Docker.
- Frontend React/Vite servido por Nginx en contenedor Docker.
- Scheduler de recordatorios mediante `cron` del host.
- Backups PostgreSQL mediante `pg_dump` diario.

VPS:

- IP pública: `66.70.190.84`
- Directorio de aplicación: `/srv/apps/turnelia`
- Compose: `/srv/apps/turnelia/docker-compose.vps.yml`
- Entorno productivo: `/srv/apps/turnelia/.env.vps`
- Proxy Caddy: `/srv/apps/proxy/Caddyfile`

Contenedores productivos:

- `turnelia-ovh-api`
- `turnelia-ovh-db`
- `turnelia-ovh-frontend`
- `caddy`

La API usa PostgreSQL interno por red Docker (`db:5432/turnelia`). Producción ya no depende de Aiven.

## 3. Dominios y Cloudflare

Dominios productivos finales:

- `https://turnelia.com.ar` → frontend OVH.
- `https://www.turnelia.com.ar` → redirección permanente a `https://turnelia.com.ar`.
- `https://api.turnelia.com.ar` → API OVH.

Dominios técnicos mantenidos temporalmente:

- `https://ovh.turnelia.com.ar`
- `https://api-ovh.turnelia.com.ar`

Estos dominios técnicos apuntan al mismo despliegue y no duplican aplicaciones, datos ni consumo de almacenamiento significativo.

### Cambio DNS realizado

Durante el cutover se reemplazaron referencias a Render por OVH:

- `api.turnelia.com.ar` pasó de CNAME a Render a `A 66.70.190.84`.
- `turnelia.com.ar` pasó de Render/flattening de Cloudflare a `A 66.70.190.84`.
- `www.turnelia.com.ar` quedó como CNAME hacia `turnelia.com.ar`.
- Se mantuvo `DNS only` durante el cutover y emisión de certificados.

No se modificaron los registros de correo de Resend ni otros registros de validación existentes.

Antes del cambio, el dominio raíz resolvía a IPs de Render (`216.24.57.7` / `216.24.57.15`).

## 4. Caddy y HTTPS

Caddy comparte el VPS con otros proyectos, por lo que los bloques de Turnelia se incorporaron sin modificar los bloques de Orienta.

Configuración productiva relevante:

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

Se mantuvieron adicionalmente los bloques de staging/técnicos:

```caddyfile
ovh.turnelia.com.ar {
    reverse_proxy turnelia-ovh-frontend:80
}

api-ovh.turnelia.com.ar {
    reverse_proxy turnelia-ovh-api:8000
}
```

Durante el cutover Caddy intentó emitir certificados antes de que todos los DNS hubieran propagado. Let's Encrypt rechazó temporalmente challenges HTTP-01/TLS-ALPN porque los dominios todavía llegaban a Render. Después de mover cada DNS al VPS, Caddy obtuvo automáticamente certificados válidos.

Validaciones finales:

```bash
curl -i https://api.turnelia.com.ar/health/ready
curl -I https://turnelia.com.ar
curl -I https://www.turnelia.com.ar
```

Resultados verificados:

- API: HTTP/2 200 y `{"status":"ok"}`.
- Frontend: HTTP/2 200.
- `www`: HTTP/2 301 hacia `https://turnelia.com.ar/`.

## 5. Migración PostgreSQL

### Backups previos

Se realizaron backups antes de cualquier restore destructivo.

Backup Aiven inicial:

- `turnelia_aiven_20260904_212403.dump`
- SHA256: `c69b0fb6d38cf65e32697bcc3a3371377cac9df7ffd98d9e666645e1a64a62d8`

El backup inicial fue copiado también a una estación Windows mediante `scp` y se verificó el SHA256 fuera del VPS.

Backup VPS previo al restore final:

- `turnelia_vps_pre_final_20260905_200247.dump`
- SHA256: `c439584b4815081c1845d7db81fb2537dc99ddba9b1c4652cf72b5b415925e2d`

Snapshot Aiven pre-cutover:

- `turnelia_FINAL_20260905_200247.dump`
- SHA256: `a4d2d0e0dc36639b16c5332e37254a99a3abb807ea80e2663d792e2eebd474eb`

### Cutover final

Antes del dump final:

1. Se suspendió la API de Render.
2. Se suspendió el cron de recordatorios de Render.
3. Se confirmó que la API antigua devolvía `HTTP 503` con `x-render-routing: suspend-by-user`.
4. Recién entonces se tomó el dump final de Aiven.

Dump final:

- `turnelia_CUTOVER_20260905_201521.dump`
- SHA256: `83d40203b35b8b70e4f53901c166ad004cdc3bc8320ef300a6deb7baca5382e8`

Se detuvo la API OVH, se recreó la base `turnelia`, se restauró el dump final y se inició nuevamente la API.

### Conteos verificados en cutover

Aiven y OVH quedaron iguales en:

| Tabla | Filas |
|---|---:|
| appointment_reminders | 19 |
| cuentas | 10 |
| evoluciones_clinicas | 5 |
| notifications | 1 |
| pacientes | 17 |
| pagos | 0 |
| profesionales | 10 |
| suscripciones | 10 |
| turnos | 43 |
| usuarios | 7 |

Versión Alembic verificada en origen y destino:

```text
m3b4c5d6e7f8
```

Después del cutover se generaron nuevas altas directamente en OVH, por lo que Aiven dejó de ser una copia sincronizada de producción.

## 6. Variables de entorno productivas

El archivo productivo es:

```text
/srv/apps/turnelia/.env.vps
```

No se versiona.

Cambios principales respecto del staging previo:

```text
APP_ENV=production
FRONTEND_URL=https://turnelia.com.ar
PUBLIC_API_URL=https://api.turnelia.com.ar
MERCADOPAGO_ENV=production
VITE_API_URL=https://api.turnelia.com.ar
```

CORS incluye los orígenes productivos y, temporalmente, el dominio técnico OVH.

La plantilla versionada es `.env.vps.example`. Los valores reales de JWT, PostgreSQL, Resend y Mercado Pago nunca deben copiarse a documentación o commits.

## 7. Mercado Pago

Durante el cutover se reemplazó la configuración sandbox por credenciales productivas de Mercado Pago.

Familia utilizada para suscripciones SaaS:

```text
MERCADOPAGO_ACCESS_TOKEN
MERCADOPAGO_PUBLIC_KEY
MERCADOPAGO_WEBHOOK_SECRET
MERCADOPAGO_ENV
VITE_MERCADOPAGO_PUBLIC_KEY
```

Se confirmó que la Public Key de frontend pertenece a la misma aplicación productiva que las credenciales del backend.

Planes productivos restaurados:

| Plan | Importe | Moneda | Estado |
|---|---:|---|---|
| profesional | 34900.00 | ARS | activo |
| consultorio | 69900.00 | ARS | activo |
| centro | 149900.00 | ARS | activo |

Cada plan conserva su `mp_preapproval_plan_id` productivo.

### Prueba real

Se realizó una asociación real de medio de pago en producción.

Una primera tarjeta fue rechazada por Mercado Pago con:

```text
CC_VAL_433 Credit card validation has failed
```

Esto permitió verificar que frontend, backend y API de Mercado Pago estaban conectados correctamente.

La segunda prueba fue aceptada. La suscripción de prueba quedó persistida con:

```text
plan_code=profesional
status=trial
billing_provider=mercadopago
mp_status=authorized
```

También quedaron presentes `mp_preapproval_id`, `mp_preapproval_plan_id`, `trial_ends_at` y `next_payment_at`.

La cuenta continúa en trial y el primer cobro queda programado para el final del período de prueba.

## 8. Resend y emails

Configuración productiva verificada:

```text
EMAIL_PROVIDER=resend
EMAIL_FROM=Turnelia <no-reply@mail.turnelia.com.ar>
FRONTEND_URL=https://turnelia.com.ar
```

No se modificaron los registros DNS de Resend durante el cutover.

Se validó el flujo real de recuperación de contraseña:

1. solicitud desde Turnelia;
2. email recibido correctamente;
3. remitente `Turnelia <no-reply@mail.turnelia.com.ar>`;
4. enlace hacia `https://turnelia.com.ar/reset-password?...`;
5. apertura y restablecimiento sin errores.

## 9. Recordatorios automáticos

Render ejecutaba:

```text
python -m app.scripts.process_appointment_reminders
```

cada 15 minutos.

El script ejecuta una pasada y finaliza, por lo que en OVH se reemplazó Render Cron por cron del host.

Crontab productivo:

```cron
*/15 * * * * cd /srv/apps/turnelia && /usr/bin/docker compose --env-file .env.vps -f docker-compose.vps.yml --profile reminders run --rm reminders >> /var/log/turnelia-reminders.log 2>&1
```

La ejecución automática fue verificada en `journalctl` y el job terminó sin errores.

Render Cron permanece suspendido para evitar ejecuciones duplicadas.

## 10. Backups automáticos

Script del host:

```text
/usr/local/bin/backup-turnelia.sh
```

Destino:

```text
/srv/apps/turnelia/backups/automatic
```

Características:

- `pg_dump` custom format (`-Fc`).
- SHA256 por cada dump.
- retención local: 14 días.
- ejecución diaria.

Crontab:

```cron
30 3 * * * /usr/local/bin/backup-turnelia.sh >> /var/log/backup-turnelia.log 2>&1
```

Primer backup manual verificado:

```text
turnelia_20260906_021343.dump
```

El checksum fue validado correctamente.

El VPS también dispone de backups/snapshots del proveedor OVH, pero el dump PostgreSQL local es una capa independiente de recuperación.

## 11. Seguridad del VPS

Configuración operativa verificada:

- UFW activo.
- política de entrada restrictiva.
- OpenSSH permitido.
- Fail2ban activo con jail `sshd`.
- Docker activo y habilitado.
- HTTPS gestionado por Caddy.

Las credenciales productivas no se guardan en Git.

## 12. Health check operativo

Se creó:

```text
/usr/local/bin/health-vps.sh
```

Con alias recomendado:

```bash
health
```

El script comprueba:

- uptime y load average;
- disco;
- RAM;
- Docker;
- contenedores esperados;
- API y DB de Turnelia;
- Orienta;
- cron;
- ejecución reciente de reminders;
- backups y SHA256;
- UFW;
- Fail2ban;
- espacio Docker;
- errores recientes de la API.

Primera ejecución final tras la migración:

```text
OK:      25
WARN:    0
ERROR:   0
ESTADO GENERAL: SALUDABLE
```

Snapshot de recursos en esa verificación:

- Disco raíz: 15 % usado, ~62 GB libres.
- RAM: 14 % usada, ~6.6 GB disponibles.
- Load average: prácticamente nulo.

## 13. Estado de Render y Aiven después del cutover

Render API:

```text
HTTP/2 503
x-render-routing: suspend-by-user
```

Render Cron: suspendido.

Aiven:

- permanece temporalmente disponible como referencia/contingencia;
- no recibe tráfico productivo;
- la API OVH no utiliza Aiven.

No eliminar Render/Aiven inmediatamente. Se recomienda conservarlos 24-48 horas o el período operativo que se considere prudente antes de la baja definitiva.

## 14. Rollback

### Antes de aceptar escrituras en OVH

Era posible volver DNS a Render y reanudar API/Cron usando Aiven.

### Después de aceptar escrituras en OVH

Ese rollback directo **ya no es seguro**, porque la base OVH contiene datos posteriores al cutover que Aiven no conoce.

Ante una contingencia posterior al cutover:

1. congelar escrituras;
2. tomar dump inmediato de PostgreSQL OVH;
3. decidir si se recupera el servicio en el propio VPS o se restaura/sincroniza la base hacia otra infraestructura;
4. no apuntar Render a la antigua base Aiven sin reconciliar datos.

## 15. Comandos operativos útiles

Estado de Turnelia:

```bash
cd /srv/apps/turnelia
docker compose --env-file .env.vps -f docker-compose.vps.yml ps
```

Health público:

```bash
curl -s https://api.turnelia.com.ar/health/ready
```

Logs API:

```bash
docker logs --tail 100 turnelia-ovh-api
```

Logs Caddy:

```bash
docker logs --tail 100 caddy
```

Recordatorios:

```bash
tail -n 50 /var/log/turnelia-reminders.log
```

Backups:

```bash
ls -lh /srv/apps/turnelia/backups/automatic
```

Diagnóstico completo:

```bash
health
```

## 16. Estado final

Al finalizar la migración se verificó:

- frontend productivo en OVH;
- API productiva en OVH;
- PostgreSQL productivo en OVH;
- DNS productivo apuntando a OVH;
- certificados HTTPS válidos;
- login, dashboard, agenda y pacientes operativos;
- Mercado Pago productivo operativo;
- Resend productivo operativo;
- recuperación de contraseña completa;
- reminders ejecutándose en cron del VPS;
- backups diarios con checksum;
- UFW y Fail2ban activos;
- Render API y cron suspendidos;
- Aiven fuera del circuito productivo.

**Turnelia quedó migrada productivamente a OVH.**
