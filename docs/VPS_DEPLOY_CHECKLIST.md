# Turnelia VPS Deploy Checklist

Checklist operativo para despliegues y cambios de configuración en el VPS productivo de Turnelia.

Estado de referencia: **producción en OVH desde 2026-09-05/06**.

## 1. Antes de desplegar

Trabajar desde una rama `feature/`, `fix/`, `chore/` o `docs/` y verificar:

```bash
git status
git branch --show-current
git pull --ff-only
```

El working tree debe estar limpio antes de comenzar.

## 2. Validar variables de entorno

Producción usa:

```text
/srv/apps/turnelia/.env.vps
```

Antes de cualquier build o recreación:

```bash
python3 scripts/check_env_duplicates.py .env.vps
```

Esperado:

```text
[OK] Sin variables duplicadas: .env.vps
```

No continuar si hay variables duplicadas.

Variables especialmente sensibles:

- `DATABASE_URL`
- `FRONTEND_URL`
- `PUBLIC_API_URL`
- `CORS_ALLOWED_ORIGINS`
- `RESEND_API_KEY`
- `MERCADOPAGO_ACCESS_TOKEN`
- `MERCADOPAGO_PUBLIC_KEY`
- `MERCADOPAGO_WEBHOOK_SECRET`
- `VITE_API_URL`
- `VITE_MERCADOPAGO_PUBLIC_KEY`

La plantilla versionada es `.env.vps.example`.

## 3. Validar Docker Compose

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml config
```

Revisar servicios:

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml ps
```

Esperado:

- `turnelia-ovh-api`: healthy.
- `turnelia-ovh-db`: healthy.
- `turnelia-ovh-frontend`: running.

## 4. URLs productivas

```text
https://turnelia.com.ar
https://www.turnelia.com.ar
https://api.turnelia.com.ar
```

Accesos técnicos temporales:

```text
https://ovh.turnelia.com.ar
https://api-ovh.turnelia.com.ar
```

Health productivo:

```bash
curl -s https://api.turnelia.com.ar/health/ready
```

Esperado:

```json
{"status":"ok"}
```

## 5. Mercado Pago

Producción debe usar:

```text
MERCADOPAGO_ENV=production
```

Frontend y backend deben pertenecer a la misma aplicación Mercado Pago.

Planes productivos actuales:

- profesional: ARS 34.900.
- consultorio: ARS 69.900.
- centro: ARS 149.900.

Una asociación correcta debe persistir:

- `billing_provider=mercadopago`
- `mp_preapproval_id`
- `mp_preapproval_plan_id`
- `mp_status=authorized` cuando corresponda
- `next_payment_at`

No confundir la familia de variables de suscripciones SaaS `MERCADOPAGO_*` con integraciones legacy que puedan usar otros nombres.

## 6. Webhooks Mercado Pago

URL productiva esperada para suscripciones:

```text
https://api.turnelia.com.ar/webhooks/mercadopago/suscripciones
```

La clave configurada en Mercado Pago debe coincidir con:

```text
MERCADOPAGO_WEBHOOK_SECRET
```

Después de cambiar configuración backend recrear sólo la API:

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml build api
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d api
```

## 7. Resend

Producción debe tener:

```text
EMAIL_PROVIDER=resend
EMAIL_FROM=Turnelia <no-reply@mail.turnelia.com.ar>
```

Verificar periódicamente un flujo real que genere email, por ejemplo recuperación de contraseña.

El enlace generado debe usar `https://turnelia.com.ar`.

## 8. Recordatorios

Render Cron está suspendido. El único scheduler productivo debe ser el cron del VPS:

```cron
*/15 * * * * cd /srv/apps/turnelia && /usr/bin/docker compose --env-file .env.vps -f docker-compose.vps.yml --profile reminders run --rm reminders >> /var/log/turnelia-reminders.log 2>&1
```

Comprobar:

```bash
journalctl -u cron --since "40 minutes ago" --no-pager | grep turnelia
tail -n 50 /var/log/turnelia-reminders.log
```

No reactivar simultáneamente el cron de Render.

## 9. Backups

Script:

```text
/usr/local/bin/backup-turnelia.sh
```

Crontab:

```cron
30 3 * * * /usr/local/bin/backup-turnelia.sh >> /var/log/backup-turnelia.log 2>&1
```

Comprobar:

```bash
ls -lh /srv/apps/turnelia/backups/automatic
```

Cada dump debe tener `.sha256` asociado.

## 10. Caddy y HTTPS

Caddy es compartido con otros proyectos. No sobrescribir bloques ajenos.

Validar:

```bash
docker exec caddy caddy validate --config /etc/caddy/Caddyfile
```

Recargar:

```bash
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

Comprobar:

```bash
curl -I https://turnelia.com.ar
curl -I https://www.turnelia.com.ar
curl -i https://api.turnelia.com.ar/health/ready
```

## 11. Deploy seguro backend

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml build api
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d api
```

Después:

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml ps
curl -s https://api.turnelia.com.ar/health/ready
```

## 12. Deploy seguro frontend

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml build frontend
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d frontend
```

Después:

```bash
curl -I https://turnelia.com.ar
```

## 13. Regla crítica de base de datos

No ejecutar:

```bash
docker compose down -v
```

porque puede eliminar los volúmenes persistentes.

Antes de restores, recreaciones o cambios destructivos generar un dump verificable.

## 14. Health check general

Ejecutar:

```bash
health
```

El script `/usr/local/bin/health-vps.sh` comprueba recursos, Docker, Turnelia, Orienta, cron, reminders, backups, checksum, UFW, Fail2ban y logs recientes.

Un estado normal debe terminar en:

```text
ESTADO GENERAL: SALUDABLE
```

## 15. Infraestructura legacy

Render API: suspendida.  
Render Cron: suspendido.  
Aiven: fuera del circuito productivo.

Después del cutover OVH recibe nuevas escrituras, por lo que Aiven no debe tratarse como réplica sincronizada.

## 16. Checklist final de cada deploy

- [ ] repo actualizado y working tree limpio
- [ ] `.env.vps` sin variables duplicadas
- [ ] `docker compose ... config` válido
- [ ] servicio modificado reconstruido y recreado
- [ ] API healthy
- [ ] DB healthy
- [ ] frontend accesible
- [ ] HTTPS correcto
- [ ] login funciona
- [ ] funciones afectadas por el cambio probadas
- [ ] cron de reminders sigue activo
- [ ] backup reciente disponible
- [ ] `health` sin errores críticos

## 17. Referencias

- `docs/MIGRATION_RENDER_AIVEN_TO_OVH.md`
- `docs/DEPLOYMENT.md`
- `docs/OPERATIONS_VPS.md`
- `docs/CURRENT_STATE.md`
