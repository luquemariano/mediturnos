# Turnelia VPS Deploy Checklist

Checklist operativo para despliegues y cambios de configuración en el VPS de Turnelia.

## 1. Antes de desplegar

Trabajar siempre desde una rama `feature/` o `chore/` y verificar:

```bash
git status
git branch --show-current
git pull --ff-only
```

El working tree debe estar limpio antes de comenzar.

## 2. Validar variables de entorno

Antes de cualquier build o recreación de servicios en el VPS:

```bash
python3 scripts/check_env_duplicates.py .env.vps
```

La validación debe terminar con:

```text
[OK] Sin variables duplicadas: .env.vps
```

No continuar el deploy si hay variables duplicadas.

Variables especialmente sensibles a duplicación:

- `MERCADOPAGO_ACCESS_TOKEN`
- `MERCADOPAGO_PUBLIC_KEY`
- `MERCADOPAGO_WEBHOOK_SECRET`
- `VITE_MERCADOPAGO_PUBLIC_KEY`
- `DATABASE_URL`
- `FRONTEND_URL`
- `PUBLIC_API_URL`

En la notebook, donde `.env.vps` no existe, validar la plantilla con:

```powershell
python scripts/check_env_duplicates.py .env.vps.example
```

## 3. Validar configuración efectiva de Docker Compose

Antes de recrear servicios:

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml config
```

Para revisar una variable puntual:

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml config | grep NOMBRE_VARIABLE
```

## 4. Mercado Pago en staging

Staging utiliza:

```text
MERCADOPAGO_ENV=sandbox
```

Las credenciales deben pertenecer a la misma aplicación Seller Test.

La Public Key usada por el frontend y el Access Token usado por el backend deben pertenecer a la misma aplicación.

## 5. Webhooks Mercado Pago

URL de staging:

```text
https://api-ovh.turnelia.com.ar/webhooks/mercadopago/suscripciones
```

Eventos habilitados:

- Planes y suscripciones
- Pagos (legacy)

La clave secreta configurada en Mercado Pago debe coincidir con:

```text
MERCADOPAGO_WEBHOOK_SECRET
```

Después de modificar esta variable hay que recrear la API:

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d api
```

## 6. Verificación de servicios

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml ps
```

Esperado:

- `turnelia-ovh-api`: healthy
- `turnelia-ovh-db`: healthy
- `turnelia-ovh-frontend`: running

Healthcheck público:

```bash
curl -s https://api-ovh.turnelia.com.ar/health/ready
```

Esperado:

```json
{"status":"ok"}
```

## 7. Validación de suscripción Mercado Pago

Una suscripción creada correctamente debe tener:

- `mp_preapproval_id`
- `mp_preapproval_plan_id`
- `mp_status=authorized`
- monto y moneda configurados
- próxima fecha de pago

## 8. Validación de cobros

Un cobro exitoso debe mostrar:

```text
status=processed
payment.status=approved
payment.status_detail=accredited
```

## 9. Validación de Webhooks

Los eventos recibidos deben quedar registrados en:

```text
notificaciones_mercadopago_suscripcion
```

con:

```text
processing_status=processed
```

Los pagos deben quedar registrados en:

```text
cobros_suscripcion
```

con:

```text
status=approved
status_detail=accredited
```

## 10. Deploy seguro

Para cambios de backend:

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml build api
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d api
```

Para cambios de frontend:

```bash
docker compose --env-file .env.vps -f docker-compose.vps.yml build frontend
docker compose --env-file .env.vps -f docker-compose.vps.yml up -d frontend
```

Evitar recrear servicios que no cambiaron.

## 11. Regla crítica de base de datos

No ejecutar:

```bash
docker compose down -v
```

porque elimina volúmenes persistentes.

## 12. Checklist final

- [ ] `.env.vps` sin variables duplicadas
- [ ] Docker Compose resuelve correctamente las variables
- [ ] API healthy
- [ ] DB healthy
- [ ] frontend accesible
- [ ] `/health/ready` responde OK
- [ ] login funciona
- [ ] suscripción puede crearse
- [ ] Mercado Pago devuelve preapproval autorizado
- [ ] cobro aprobado registrado
- [ ] webhook validado y procesado
