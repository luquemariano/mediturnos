# Operación diaria de Turnelia en OVH

Estado: **productivo**  
Fecha de referencia: **2026-09-06**

Este runbook resume las tareas habituales de operación del VPS después de la migración desde Render/Aiven.

## 1. Acceso

Servidor:

```text
66.70.190.84
```

Aplicación:

```text
/srv/apps/turnelia
```

## 2. Comando de salud

Se instaló:

```text
/usr/local/bin/health-vps.sh
```

Alias recomendado:

```bash
health
```

El resultado esperado en operación normal es:

```text
ESTADO GENERAL: SALUDABLE
```

El script revisa:

- uptime;
- carga del sistema;
- disco;
- RAM;
- Docker;
- contenedores esperados;
- API y PostgreSQL de Turnelia;
- HTTPS de Orienta;
- cron;
- reminders;
- backups y checksum;
- UFW;
- Fail2ban;
- espacio usado por Docker;
- errores recientes de la API.

## 3. Estado Docker

```bash
cd /srv/apps/turnelia
docker compose --env-file .env.vps -f docker-compose.vps.yml ps
```

Esperado:

- `turnelia-ovh-api`: healthy.
- `turnelia-ovh-db`: healthy.
- `turnelia-ovh-frontend`: running.

Todos los contenedores del VPS:

```bash
docker ps
```

## 4. Health API

```bash
curl -s https://api.turnelia.com.ar/health/ready
```

Esperado:

```json
{"status":"ok"}
```

Dominios técnicos:

```bash
curl -I https://ovh.turnelia.com.ar
curl -i https://api-ovh.turnelia.com.ar/health/ready
```

## 5. Logs

API:

```bash
docker logs --tail 100 turnelia-ovh-api
```

Seguimiento en vivo:

```bash
docker logs -f turnelia-ovh-api
```

Caddy:

```bash
docker logs --tail 100 caddy
```

Recordatorios:

```bash
tail -n 50 /var/log/turnelia-reminders.log
```

Backups:

```bash
tail -n 50 /var/log/backup-turnelia.log
```

Cron:

```bash
journalctl -u cron --since "1 hour ago" --no-pager
```

## 6. Recordatorios

Programación:

```cron
*/15 * * * * cd /srv/apps/turnelia && /usr/bin/docker compose --env-file .env.vps -f docker-compose.vps.yml --profile reminders run --rm reminders >> /var/log/turnelia-reminders.log 2>&1
```

Prueba manual:

```bash
cd /srv/apps/turnelia
docker compose --env-file .env.vps -f docker-compose.vps.yml --profile reminders run --rm reminders
```

Código de salida esperado:

```bash
echo $?
```

Debe ser `0`.

## 7. Backups

Script:

```text
/usr/local/bin/backup-turnelia.sh
```

Programación:

```cron
30 3 * * * /usr/local/bin/backup-turnelia.sh >> /var/log/backup-turnelia.log 2>&1
```

Ejecutar manualmente:

```bash
sudo /usr/local/bin/backup-turnelia.sh
```

Listar backups:

```bash
ls -lh /srv/apps/turnelia/backups/automatic
```

Los backups deben tener su `.sha256` asociado.

Retención local actual: 14 días.

## 8. Disco y Docker

Disco:

```bash
df -h
```

Docker:

```bash
docker system df
```

Durante la primera revisión posterior al cutover Docker reportó varios GB recuperables entre imágenes y build cache, pero el disco raíz estaba sólo al 15 %. No ejecutar limpiezas agresivas sólo por el porcentaje reclaimable.

Antes de cualquier limpieza revisar qué está activo.

## 9. RAM y carga

```bash
free -h
uptime
```

Como referencia, la primera ejecución final del health check mostró aproximadamente:

```text
RAM usada: 14 %
Disco usado: 15 %
Load average: cercano a 0
```

## 10. Seguridad

UFW:

```bash
sudo ufw status
```

Fail2ban:

```bash
sudo fail2ban-client status sshd
```

Servicios:

```bash
systemctl status fail2ban --no-pager
systemctl status docker --no-pager
systemctl status cron --no-pager
```

## 11. Caddy

Validar configuración:

```bash
docker exec caddy caddy validate --config /etc/caddy/Caddyfile
```

Recargar después de un cambio válido:

```bash
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

No modificar ni eliminar bloques de otros proyectos al editar `/srv/apps/proxy/Caddyfile`.

## 12. Variables de entorno

Producción:

```text
/srv/apps/turnelia/.env.vps
```

Contrato versionado:

```text
.env.vps.example
```

Verificar duplicados antes de desplegar:

```bash
python3 scripts/check_env_duplicates.py .env.vps
```

Validar Compose:

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml config
```

No versionar secretos ni copiar `.env.vps` al repositorio.

## 13. Deploy backend

```bash
cd /srv/apps/turnelia
docker compose --env-file .env.vps -f docker-compose.vps.yml build api
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d api
```

Verificar:

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml ps
curl -s https://api.turnelia.com.ar/health/ready
```

## 14. Deploy frontend

```bash
cd /srv/apps/turnelia
docker compose --env-file .env.vps -f docker-compose.vps.yml build frontend
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d frontend
```

Verificar:

```bash
curl -I https://turnelia.com.ar
```

## 15. PostgreSQL

No exponer PostgreSQL públicamente sólo para administración rutinaria.

Entrar con `psql` desde el contenedor:

```bash
docker exec -it turnelia-ovh-db psql -U turnelia -d turnelia
```

Regla crítica:

```text
NO ejecutar docker compose down -v
```

porque puede eliminar el volumen persistente.

## 16. Verificación rápida semanal

```bash
health
```

Si se quiere revisar manualmente:

```bash
df -h
free -h
uptime
docker ps
curl -s https://api.turnelia.com.ar/health/ready
sudo fail2ban-client status sshd
ls -lh /srv/apps/turnelia/backups/automatic | tail
```

## 17. Render/Aiven legacy

Render API y cron están suspendidos.

Aiven está fuera del circuito productivo.

No reactivar Render Cron mientras el cron OVH esté activo, porque se generarían ejecuciones duplicadas de reminders.

No considerar Aiven como una réplica actual: después del cutover OVH empezó a recibir nuevas escrituras.

## 18. Ante una incidencia

Orden recomendado:

1. ejecutar `health`;
2. comprobar `docker ps`;
3. comprobar `/health/ready`;
4. revisar logs de API;
5. revisar logs de Caddy si el problema es HTTP/HTTPS;
6. comprobar espacio y memoria;
7. comprobar DB;
8. tomar backup antes de cualquier operación destructiva;
9. evitar un rollback hacia Aiven sin reconciliar datos posteriores al cutover.

Para la historia completa de migración consultar `docs/MIGRATION_RENDER_AIVEN_TO_OVH.md`.
