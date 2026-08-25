# Deployment de Turnelia

Estado: configuración declarada; operación externa actual **NO DETERMINADA**.

## Arquitectura declarada

- Frontend React/Vite como Render Static Site.
- Backend FastAPI en Render Web Service Docker.
- Cron de recordatorios declarado en `render.yaml`.
- PostgreSQL como motor productivo; proveedor/ubicación documentados: Aiven.
- Cloudflare documentado para DNS.
- Resend configurable para email.
- R2 configurable para object storage.
- Mercado Pago para pagos clínicos y suscripciones SaaS.

`render.yaml` declara Web Service, Static Site y Cron Job. PostgreSQL no está aprovisionado como recurso en ese archivo.

## PostgreSQL / Aiven

Aiven es el proveedor/ubicación productiva documentada por la historia operativa del proyecto, no un dato inferido de `render.yaml`. La API recibe `DATABASE_URL`; no se reproducen connection strings. Salud, credenciales y conexión actuales: **NO DETERMINADAS**.

## Render y dominios

El deployment declarado incluye `/health/ready`, rewrite frontend hacia `/index.html` y arranque Docker mediante `app.scripts.start`, que ejecuta migraciones antes de Uvicorn.

Los dominios `turnelia.com.ar` y `api.turnelia.com.ar` están documentados/configurados como referencia. Su estado operativo actual es **NO DETERMINADO**.

## Email, Mercado Pago y Cron

Resend aparece como proveedor configurable; `in_memory` existe para entornos controlados. Dominio, credenciales y entrega actuales son **NO DETERMINADOS**.

Pagos clínicos usan la familia `MERCADO_PAGO_*`; suscripciones SaaS usan `MERCADOPAGO_*`. No deben mezclarse credenciales ni ciclos de vida. Operación externa actual **NO DETERMINADA**.

El job `turnelia-appointment-reminders` ejecuta `python -m app.scripts.process_appointment_reminders` cada 15 minutos según `render.yaml`; ejecución real y entrega de emails **NO DETERMINADAS**.

## Variables de entorno

Nombres documentados: `APP_ENV`, `DATABASE_URL`, `APP_TIMEZONE`, `PORT`, `CORS_ALLOWED_ORIGINS`, `FRONTEND_URL`, `PUBLIC_API_URL`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`, `PASSWORD_RESET_EXPIRE_MINUTES`, `APPOINTMENT_ACTION_SECRET`, `STUDY_ACCESS_SECRET`, `EMAIL_PROVIDER`, `RESEND_API_KEY`, `EMAIL_FROM`, `OBJECT_STORAGE_PROVIDER`, variables `R2_*`, `MERCADO_PAGO_*`, `MERCADOPAGO_*`, `TRUST_PROXY_HEADERS`, variables `RATE_LIMIT_*` y variables demo/bootstrap. No se muestran valores.

En producción, el código valida que `APPOINTMENT_ACTION_SECRET` y `STUDY_ACCESS_SECRET` tengan al menos 32 caracteres.

## Deploy y rollback

Build, arranque y migración están documentados en `Dockerfile`, `app/scripts/start.py` y `render.yaml`. Rollback formal, recuperación y garantías operativas: **NO DETERMINADOS**.
