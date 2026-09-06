# Estado actual de Turnelia

Fecha de referencia: **2026-09-06**.

Este documento combina estado del repositorio con evidencia operativa validada durante la migración productiva a OVH.

## Convención de estados

- **IMPLEMENTADO EN CÓDIGO:** existe código y, cuando corresponde, tests.
- **DECLARADO EN CONFIGURACIÓN:** aparece en configuración de deployment o entorno, sin verificar ejecución real.
- **VERIFICADO EN PRODUCCIÓN:** comprobado mediante evidencia operativa real.
- **NO DETERMINADO:** no hay evidencia suficiente.
- **NO INCORPORADO:** capacidad prevista que todavía no existe.
- **LEGACY:** referencia histórica que ya no representa la infraestructura productiva actual.

## Estado funcional

| Área | Estado | Evidencia/límite |
|---|---|---|
| Landing, autenticación, profesionales, pacientes | VERIFICADO EN PRODUCCIÓN | Smoke test posterior al cutover |
| Agenda, turnos, prestaciones, disponibilidad | VERIFICADO EN PRODUCCIÓN | Navegación y uso posterior al cutover |
| Evoluciones y flujos clínicos | IMPLEMENTADO EN CÓDIGO | Código y tests; no todos los subflujos se repitieron durante el cutover |
| Solicitudes y carga pública de estudios | IMPLEMENTADO EN CÓDIGO | Código y tests |
| Suscripciones SaaS / Mercado Pago | VERIFICADO EN PRODUCCIÓN | Asociación real de medio de pago y persistencia `authorized` |
| Email / Resend | VERIFICADO EN PRODUCCIÓN | Recuperación de contraseña real de punta a punta |
| Recordatorios automáticos | VERIFICADO EN PRODUCCIÓN | Cron del VPS ejecutado y log sin errores |
| Backups PostgreSQL | VERIFICADO EN PRODUCCIÓN | Dump manual, SHA256 y programación diaria validados |
| R2 | DECLARADO EN CONFIGURACIÓN | Producción actual mantiene `OBJECT_STORAGE_PROVIDER=fake`; no hay uso productivo real validado |
| E2E / Playwright | IMPLEMENTADO EN CÓDIGO | Suite y CI existentes |

## Infraestructura productiva

Turnelia está desplegado en un VPS OVH con Ubuntu 24.04.

### Servicios

- Frontend: Docker + Nginx.
- API: Docker + FastAPI/Uvicorn.
- Base: PostgreSQL 18 en Docker.
- Reverse proxy / TLS: Caddy.
- DNS: Cloudflare.
- Email: Resend.
- Suscripciones: Mercado Pago.
- Recordatorios: cron del host cada 15 minutos.
- Backups: `pg_dump` diario + SHA256.

Contenedores esperados:

```text
turnelia-ovh-api
turnelia-ovh-db
turnelia-ovh-frontend
```

Caddy es compartido con otros proyectos del VPS.

## Dominios verificados

Producción:

```text
https://turnelia.com.ar
https://www.turnelia.com.ar
https://api.turnelia.com.ar
```

Técnicos/contingencia temporal:

```text
https://ovh.turnelia.com.ar
https://api-ovh.turnelia.com.ar
```

Verificaciones finales:

- `turnelia.com.ar`: HTTP/2 200.
- `www.turnelia.com.ar`: HTTP/2 301 hacia el dominio raíz.
- `api.turnelia.com.ar/health/ready`: HTTP/2 200 + `{"status":"ok"}`.
- dominios `ovh.*`: HTTP/2 200.

## PostgreSQL

Producción usa PostgreSQL local del stack Docker OVH.

La API productiva conecta contra el host interno `db:5432/turnelia`. Aiven ya no forma parte del circuito de producción.

Migración final realizada con PostgreSQL 18.6 en origen y destino y Alembic:

```text
m3b4c5d6e7f8
```

El dump final se tomó después de suspender API y cron de Render, evitando escrituras concurrentes en Aiven durante el corte.

## Mercado Pago

Entorno productivo:

```text
MERCADOPAGO_ENV=production
```

Planes productivos:

- Profesional: ARS 34.900/mes.
- Consultorio: ARS 69.900/mes.
- Centro: ARS 149.900/mes.

Se verificó una asociación real de medio de pago. La suscripción quedó persistida con:

```text
plan_code=profesional
status=trial
billing_provider=mercadopago
mp_status=authorized
```

El primer cobro queda programado al finalizar el trial.

## Resend

Verificado en producción mediante recuperación de contraseña:

```text
From: Turnelia <no-reply@mail.turnelia.com.ar>
```

El enlace generado apuntó a `https://turnelia.com.ar/reset-password` y el flujo finalizó sin errores.

## Recordatorios

Render Cron está suspendido.

OVH ejecuta cada 15 minutos:

```cron
*/15 * * * * cd /srv/apps/turnelia && /usr/bin/docker compose --env-file .env.vps -f docker-compose.vps.yml --profile reminders run --rm reminders >> /var/log/turnelia-reminders.log 2>&1
```

El cron fue comprobado mediante `journalctl` y el log del worker.

## Backups

Script:

```text
/usr/local/bin/backup-turnelia.sh
```

Programación:

```cron
30 3 * * * /usr/local/bin/backup-turnelia.sh >> /var/log/backup-turnelia.log 2>&1
```

Destino:

```text
/srv/apps/turnelia/backups/automatic
```

Política actual:

- dump PostgreSQL custom format;
- SHA256 por backup;
- retención local de 14 días.

## Health check del VPS

Script:

```text
/usr/local/bin/health-vps.sh
```

Alias operativo:

```bash
health
```

Primera validación final registrada después del cutover:

```text
OK:      25
WARN:    0
ERROR:   0
ESTADO GENERAL: SALUDABLE
```

En esa comprobación:

- disco raíz: 15 % usado;
- RAM: 14 % usada;
- carga CPU: prácticamente nula;
- UFW activo;
- Fail2ban activo;
- API y DB Turnelia healthy;
- Orienta operativo;
- reminders recientes;
- backup reciente con checksum válido.

## Infraestructura legacy

### Render

Estado: **LEGACY / SUSPENDIDO**.

La API histórica responde:

```text
HTTP/2 503
x-render-routing: suspend-by-user
```

El cron histórico también está suspendido.

### Aiven

Estado: **LEGACY / FUERA DEL CIRCUITO PRODUCTIVO**.

Se conserva temporalmente por contingencia y referencia, pero no está sincronizado con las nuevas escrituras que ocurran después del cutover en OVH.

## Rollback actual

Ya no es seguro volver simplemente DNS a Render + Aiven, porque OVH contiene escrituras posteriores al corte.

Ante una contingencia grave se debe preservar primero la base actual OVH y luego decidir restauración/sincronización.

## Documentación relacionada

- `docs/MIGRATION_RENDER_AIVEN_TO_OVH.md`: historia completa del cutover.
- `docs/DEPLOYMENT.md`: arquitectura y operación productiva actual.
- `docs/VPS_DEPLOY_CHECKLIST.md`: checklist para despliegues y verificaciones.
- `.env.vps.example`: contrato de variables productivas sin secretos.
