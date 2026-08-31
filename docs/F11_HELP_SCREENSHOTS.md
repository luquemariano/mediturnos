# F11.7 · Dataset y screenshots del Centro de Ayuda

## Estado

El fixture y la suite de generación están preparados, pero las capturas S01–S17 quedaron pendientes en esta ejecución porque el daemon de Docker no estaba disponible. La suite no usa producción ni una base compartida.

## Dataset E2E

Se reutiliza `frontend/e2e/` y el proyecto aislado `turnelia-e2e` definido por `e2e.ps1`. `app/scripts/seed_e2e.py` conserva el administrador E2E existente y agrega un profesional sintético `Laura Martínez`, tres prestaciones, seis pacientes, disponibilidad semanal, turnos relativos, resumen clínico, evoluciones y una solicitud de estudio con un documento ficticio.

Todos los emails del fixture usan `@example.com`; teléfonos, matrículas, nombres y textos clínicos son sintéticos.

## Reset y regeneración

Desde la raíz del repositorio, con Docker disponible y las variables E2E locales configuradas:

```powershell
$env:E2E_ADMIN_PASSWORD = "<secreto local>"
$env:E2E_JWT_SECRET = "<secreto local de al menos 32 caracteres>"
$env:E2E_DB_PASSWORD = "<secreto local>"
.\e2e.ps1
```

El script comprueba los puertos, recrea únicamente PostgreSQL del proyecto `turnelia-e2e`, aplica migraciones sobre esa base de test, carga el fixture y ejecuta Playwright. La suite de screenshots es `frontend/e2e/help-screenshots.spec.ts`.

## Inventario

La suite reserva estos nombres estables en `frontend/public/help/screenshots/`:

`01-onboarding-perfil.png` · `02-prestacion-crear.png` · `03-disponibilidad-semanal.png` · `04-disponibilidad-excepciones.png` · `05-agenda-dia.png` · `06-agenda-semana.png` · `07-agenda-mes.png` · `08-turno-nuevo.png` · `09-turno-reprogramar.png` · `10-pacientes-listado.png` · `11-paciente-detalle.png` · `12-resumen-clinico.png` · `13-evolucion-clinica.png` · `14-documentos.png` · `15-estudio-solicitud.png` · `16-estudio-carga-publica.png` · `17-estudio-revision.png`.

Resolución principal: `1440 × 1000`. La validación mobile prevista es `390 × 844`. No se generan PDF ni se modifican flujos productivos.
