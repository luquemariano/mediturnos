# Testing de Turnelia

Fuente canónica para validar cambios. No se declaran porcentajes de cobertura porque no están disponibles.

## Backend

Ubicación: `tests/`.

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Este comando depende de que exista el entorno virtual local `.venv` con las dependencias instaladas. Como alternativa genérica, cuando Python y las dependencias estén disponibles en el entorno activo, puede ejecutarse:

```powershell
python -m pytest
```

Ninguna de las dos formas es universalmente superior: la primera usa explícitamente el entorno virtual del repositorio y la segunda depende de la configuración activa del entorno.

`tests/conftest.py` contiene fixtures compartidos. La mayoría de pruebas usa SQLite, incluidas bases in-memory. Hay suites PostgreSQL selectivas para concurrencia, pagos, recordatorios y acciones relacionadas.

La colección cubre autenticación, recuperación, roles/ownership, profesionales, pacientes, turnos, disponibilidad, excepciones, feriados, solapamientos, concurrencia, pagos, webhooks, suscripciones, recordatorios, emails, documentos, estudios, evoluciones, perfiles clínicos, notificaciones, storage, rate limiting, health checks, seed y bootstrap.

La profundidad de cobertura varía por módulo. Consultar `tests/` para el detalle. Sólo algunos flujos cuentan con validación PostgreSQL explícita.

## Frontend

Ubicación: `frontend/tests/`. Usa Vitest, Testing Library, jsdom, TypeScript y Vite.

```powershell
Set-Location frontend
npm test
npm run lint
npm run build
```

Hay cobertura de sesión, recuperación, dashboards, agenda, pacientes, profesionales, disponibilidad, prestaciones, suscripciones, estudios, documentos, notificaciones y SEO.

La cobertura no es uniforme entre módulos. Consultar `frontend/tests/` para el detalle.

## Limitaciones actuales

- Playwright no está instalado ni configurado.
- No existe testing E2E real.
- SQLite no demuestra compatibilidad PostgreSQL total.
- Tests locales no validan la operación productiva de Render, Aiven, Resend, R2 o Mercado Pago.
- La cobertura PostgreSQL es selectiva.

## Regla para nuevas features

Toda modificación relevante debe incluir tests proporcionales al riesgo. Cambios de permisos deben cubrir casos permitidos y prohibidos; cambios de turnos, disponibilidad, estados, solapamientos y concurrencia cuando corresponda; cambios de pagos, ownership, idempotencia y webhooks.
