# SEO-DATA-01 · Google Search Console

Turnelia puede recolectar datos propios desde la API oficial de Google Search Console sin depender de servicios intermedios.

## Alcance

La integración es de solo lectura y usa exclusivamente el scope:

https://www.googleapis.com/auth/webmasters.readonly

La propiedad esperada es:

sc-domain:turnelia.com.ar

## Variables de entorno

GSC_CLIENT_ID=
GSC_CLIENT_SECRET=
GSC_REFRESH_TOKEN=
GSC_SITE_URL=sc-domain:turnelia.com.ar

Nunca versionar secretos ni JSON de credenciales OAuth.

## Bootstrap OAuth local

En Google Cloud:

1. Crear o seleccionar un proyecto para Turnelia.
2. Habilitar Google Search Console API.
3. Configurar Google Auth Platform / OAuth consent.
4. Crear un cliente OAuth de tipo Desktop app.
5. Descargar el JSON de credenciales en una ubicación local no versionada.

Luego ejecutar:

python -m app.scripts.gsc_oauth_bootstrap --credentials C:\ruta\client_secret.json --env-output C:\Proyectos\mediturnos\private\gsc\turnelia-gsc.env

El script abre Google en el navegador local, solicita solamente el scope read-only y recibe el callback en localhost.
No imprime access token, refresh token ni client secret completos.

## Recolección manual

Con las cuatro variables GSC cargadas:

python -m app.scripts.collect_gsc_snapshot --dry-run
python -m app.scripts.collect_gsc_snapshot

Defaults:
- 28 días consolidados.
- lag de 3 días.
- comparación contra los 28 días inmediatamente anteriores.
- search type web.

También acepta --days, --lag-days, --start-date, --end-date, --dry-run, --force y --output-root.

## Snapshot

Se escriben:

var/seo/gsc/latest.json
var/seo/gsc/history/YYYY-MM-DD.json

El snapshot contiene summary, daily, queries, pages, query_pages, countries, devices, opportunities y new_queries.

opportunities usa reglas transparentes: mínimo 10 impresiones y posición entre 4 y 20.

new_queries compara el período actual con el período inmediatamente anterior.

## Docker y producción

El servicio api monta:

./var/seo:/app/var/seo

Cron sugerido:

15 7 * * * cd /srv/apps/turnelia && /usr/bin/docker compose --env-file .env.vps -f docker-compose.vps.yml run --rm api python -m app.scripts.collect_gsc_snapshot >> /var/log/turnelia-gsc.log 2>&1

## Limitaciones

Search Analytics no garantiza exponer absolutamente todas las consultas. Google puede omitir filas por privacidad y aplica límites de filas.

El colector pagina en bloques de hasta 25.000 filas y posee un límite defensivo para evitar loops.

Los snapshots no contienen client secret, refresh token ni access token.
