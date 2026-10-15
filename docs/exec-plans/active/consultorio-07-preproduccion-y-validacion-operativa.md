# Entrega 07 — Preproducción aislada y validación operativa

Estado: **IMPLEMENTACIÓN LOCAL Y VALIDACIÓN AISLADA COMPLETADAS; VPS NO ACCESIBLE CON LAS CREDENCIALES DISPONIBLES**
Base: `origin/main` en `39b701f965b0f72ad3ebb4c6ffcbfe6162dfd96f`
Rama: `codex/consultorio-07-preproduccion-operativa`

## Objetivo y límites

Preparar un stack de staging aislado, datos sintéticos y procedimientos para validación operativa. No tocar producción, sus datos, servicios, secretos, DNS, Caddy, backups, correo, WhatsApp ni cobros. No enviar mensajes reales. `docs/audits/` es un directorio local no versionado y queda fuera de toda operación.

## Preflight de solo lectura y riesgos de colisión

- `origin/main` se actualizó mediante `git fetch origin main` y coincide con el SHA informado: `39b701f965b0f72ad3ebb4c6ffcbfe6162dfd96f` (merge del PR #92). La rama de trabajo fue creada desde ese commit.
- El directorio `docs/audits/` ya existía sin seguimiento; no se inspecciona su contenido ni se modifica.
- `docs/DEPLOYMENT.md` y `docs/deployment/VPS_OVH.md` documentan producción en `/srv/apps/turnelia`, Compose con contenedores de nombres fijos `turnelia-ovh-*`, PostgreSQL 18 y Caddy compartido por la red Docker externa `proxy`. El backup productivo usa `/usr/local/bin/backup-turnelia.sh` y `/srv/apps/turnelia/backups/automatic`; cron diario 03:30.
- El Compose productivo y el Compose E2E tienen puertos diferentes. El staging propuesto usa puertos loopback `18080/18081`, proyecto Compose y volumen PostgreSQL con prefijo `turnelia-staging`; no publica PostgreSQL, no se conecta a `proxy` y no monta `/srv/apps/turnelia` ni sus backups.
- DNS de solo lectura: `turnelia.com.ar` y `api.turnelia.com.ar` resolvieron a `66.70.190.84`; `staging.turnelia.com.ar` no devolvió registro. `https://api.turnelia.com.ar/health/ready` respondió HTTP 200. `https://staging.turnelia.com.ar/robots.txt` no pudo resolverse.
- El intento de SSH de solo lectura al host resuelto `66.70.190.84`, usuario `root`, fue rechazado: `Permission denied (publickey,password)`. No hay alias/Host configurado en `%USERPROFILE%\.ssh\config`. Por eso no se pudieron verificar el estado vivo de Docker/Caddy/puertos, los volúmenes/backups/cron, recursos libres del VPS ni configuraciones activas de Resend/WABA. Los datos correspondientes se marcan **NO VERIFICADOS EN VPS** y no se crean recursos remotos.
- `docs/DEPLOYMENT.md` registra Resend productivo y el Compose versionado tiene proveedor WhatsApp configurable; no se leyó `.env.vps`, Caddyfile remoto, backups ni secretos. No se presume que exista Meta App/número de prueba separado.

### Riesgos antes de provisionar

1. Colisión con producción si el staging reutiliza nombres fijos, la red `proxy`, el directorio `.env.vps`, la base/volumen productivos o puertos públicos. Se evita por aislamiento de proyecto/red/volumen, puertos loopback y archivos separados.
2. Envío accidental de correo si Resend queda habilitado sin control de destinatarios. Staging inicia con `in_memory`; el envío real requiere una variable explícita, API key dedicada y allowlist no vacía, y el provider valida cada destinatario.
3. Tráfico de WhatsApp a la WABA oficial. Staging inicia con proveedor fake y WhatsApp deshabilitado. Meta sólo puede habilitarse con bandera staging explícita, HTTPS `api.staging.turnelia.com.ar`, token/app secret dedicados y IDs de número/cuenta coincidentes con allowlists; no se acepta una configuración implícita.
4. Exposición/indexación de staging. El stack local lleva `noindex`, `robots.txt` bloqueado y analítica desactivada. DNS/TLS/Caddy no se configuran sin acceso y comprobación de estado.
5. Restaurar una copia productiva en el lugar incorrecto. No se leerán ni copiarán backups de producción. Una prueba de backup/restore, si se ejecuta, opera sobre datos sintéticos dentro de la base exclusiva del proyecto staging.

## Diseño del stack y datos

- Compose independiente con proyecto `turnelia-staging`, servicios sin `container_name`, red interna propia, PostgreSQL exclusivo y volúmenes exclusivos. PostgreSQL no publica puertos. API/frontend se enlazan sólo a loopback.
- Configuración `.env.staging` fuera de Git, creada con generador que no sobrescribe archivos y permisos restrictivos; secretos sintéticos aleatorios, nunca compartidos con producción.
- `APP_ENV=staging` valida PostgreSQL/base/host esperados, URLs locales o del subdominio staging, secretos fuertes, MP sandbox, email falso por defecto y WhatsApp fake/deshabilitado; Meta de prueba requiere habilitación explícita y allowlists de IDs.
- Semilla habilitada explícitamente en staging, idempotente y con guardas de host/base/APP_ENV. Sólo identidades `example.invalid`/`example.com`, contraseñas sintéticas configuradas externamente y relaciones clínicas ficticias. Incluye administradora, perfiles clínico y estética sin matrícula, paciente sintético, Consultorio/cupo/sala, ocurrencias y estado de invitación/aceptación.
- No se adjunta Caddy a la red del staging por defecto. Para publicar, requieren intervención externa: acceso SSH autorizado; confirmar puertos/red/memoria/espacio; crear registro DNS staging; preparar un bloque Caddy aislado y validarlo antes de recargar. Nunca editar ni recargar Caddy sin inspeccionar su configuración y proceso actuales.

## Implementación incremental

### 07A — Aislamiento y configuración

1. Completar inspección documental, DNS y disponibilidad de acceso remoto de solo lectura.
2. Crear este plan antes de recursos. Preparar Compose, ejemplo de entorno, generador de secretos, Nginx noindex y validación de configuración.
3. Agregar `APP_ENV=staging` con límites fail-closed para DB, email, dominios, pagos y WhatsApp.

### 07B — Datos y procedimientos sintéticos

1. Semilla idempotente bajo guarda explícita y pruebas de rechazo si apunta a desarrollo, producción o DB incorrecta.
2. Scripts/procedimientos para `up`, health, logs sanitizados, backup/restore sintético, rollback de imagen y limpieza selectiva sólo del proyecto staging.
3. Semilla/Playwright que cubre registro clínico y estética, login/onboarding, reserva/confirmación/reprogramación/cancelación, aislamiento, Consultorio/invitación y autorización negativa.

### 07C — Integraciones controladas

1. Pruebas de email con proveedor en memoria; plantillas/enlaces y tokens comprobados sin registrarlos. Variable dedicada para Resend con allowlist de destinatarios y apagado por defecto.
2. WhatsApp fake local: recordar, eventos entrantes de confirmar/cancelar, firma e idempotencia mediante suites existentes. Dejar Meta staging desactivada por defecto; para habilitarla se requieren IDs dedicados en allowlist, credenciales de Meta App/número de prueba y webhook público propio.

### 07D — Documentación y validación

1. Actualizar documentos canónicos operativos/seguridad/calidad y este plan.
2. Ejecutar suites completas solicitadas, Compose config en modo silencioso, prueba aislada de PostgreSQL/restore y `git diff --check`.
3. Revisión de seguridad; commit, push, PR a `main`, esperar Backend/PostgreSQL/Frontend/Playwright verdes. No mergear ni desplegar.

## Criterios de aceptación

- Pruebas comprueban que Compose y guardas de runtime no usan contenedor/red/volumen/base de producción, no conectan a producción, y no permiten Resend/Meta accidental.
- La base staging se crea vacía, migra y recibe únicamente fixture sintético idempotente. Nunca se ejecuta restore desde backup productivo.
- El correo falso permite verificar contenido/enlaces en pruebas; Resend sólo acepta destinatarios exactos de allowlist y permanece inactivo por defecto.
- WhatsApp fake valida idempotencia/acciones; WABA y webhook productivos no cambian.
- El stack remoto sólo se crea si el acceso permite inspección de solo lectura suficiente y se puede probar que nombres, red, puertos, volúmenes y rutas no colisionan. En caso contrario, dejar stack versionado listo y registrar el paso de infraestructura pendiente.

### Datos/acciones pendientes para una prueba remota o de integración real

- Cuenta SSH nominal con llave pública autorizada y permisos de sólo lectura para la primera inspección; después, autorizar explícitamente el alcance de escritura para crear únicamente `/srv/apps/turnelia-staging` y recursos con prefijo `turnelia-staging`.
- Confirmar/crear DNS `staging.turnelia.com.ar` apuntando al VPS elegido. Luego se vuelve a inspeccionar Caddy y sólo se configura un sitio separado tras revisar puertos, recursos y TLS.
- Para email: dirección de prueba explícitamente aprobada por Mariano, remitente verificado, API key de Resend exclusiva de staging; configurar allowlist con esa sola dirección. La bandera de envío seguirá apagada hasta esa aprobación.
- Para WhatsApp: confirmar si existe Meta App y número de test separados; aportar IDs de teléfono y Business Account, token de acceso, verify token, app secret, versión Graph y teléfono receptor controlado. El sistema exige confirmación explícita de test y coincidencia exacta de los IDs con sus allowlists.
- Estos datos no autorizan tocar producción ni enviar mensajes por sí solos. La configuración productiva, WABA oficial y sus webhooks permanecen fuera de alcance.

## Estado de evidencia

- Preflight local/lectura de DNS y health completado; acceso SSH rechazado y staging DNS ausente.
- No se creó ni modificó recurso en VPS; no se contactaron Resend/Meta, no se enviaron mensajes ni se accedió a datos/credenciales/backups productivos. Meta de prueba separada queda NO DETERMINADO: sin acceso a Business Manager no se puede constatar si ya existe app/número aislados.
- Stack local validado: Compose privado, PostgreSQL 18 healthy, Alembic `a7b8c9d0e1f2`, seed sintético idempotente repetido dos veces, API/frontend healthy en loopback, `robots.txt` bloqueado y cabecera noindex.
- Backup + SHA-256 + restore-check correctos en la DB sintética de staging; revisión restaurada `a7b8c9d0e1f2`.
- `remove` validó etiquetas, nombres de volúmenes/redes y servicios permitidos antes de retirar sólo el proyecto staging local; no quedaron contenedores, volúmenes ni redes con el prefijo/proyecto staging.
- Backend completo: `931 passed, 39 skipped, 9 warnings`; Vitest: `416 passed` en 52 archivos; staging focalizado: `19 passed, 1 warning`; PostgreSQL CI equivalente en PostgreSQL 17: `36 passed, 1 warning`; `verify.ps1 -Full` y `verify.ps1 -E2E` exitosos; Playwright `12 passed`.
- Un primer arranque identificó el requisito de PostgreSQL 18 de montar `/var/lib/postgresql`; se corrigió el Compose y se repitió la validación exitosamente.
- Las capturas de ayuda reescritas por el test documental Playwright se restauraron al estado previo.
- Build frontend aprobado con warning preexistente de chunk JavaScript >500 KB; `npm ci` notificó 7 advisories de dependencias (1 low, 2 moderate, 4 high), sin aplicar upgrades fuera de alcance.
- Verificación sintáctica Bash/Python y `git diff --check`: correctos; Git sólo avisó sobre normalización CRLF futura de documentos modificados.
- Revisión de seguridad, git diff --check, commit, push, PR y CI: pendientes.
