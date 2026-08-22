# Exec Plan: PostgreSQL CI

Estado: EN CURSO

## Objetivo

Agregar un job informativo separado de GitHub Actions que valide migraciones y
flujos PostgreSQL seleccionados sobre una base efímera de CI. PostgreSQL CI no
será required en Branch Protection en esta fase.

## Arquitectura

- Job visible: `PostgreSQL CI`.
- Runner: `ubuntu-latest`, Python 3.14, igual que `Backend CI`.
- Service container: `postgres:17-alpine`, sin volumen persistente.
- Conexión: localhost:5432 mediante `postgresql+psycopg`.
- Sin Aiven, Render, Mercado Pago, Resend, R2 ni otros servicios externos.

## Alembic y pytest

El job ejecuta `alembic heads`, `alembic upgrade head` y `alembic current`
antes de pytest. Alembic valida migraciones reales sobre PostgreSQL vacío;
pytest valida comportamiento PostgreSQL. Los fixtures pueden usar
`Base.metadata.create_all/drop_all`, por lo que no se afirma que cada test use
todo el esquema migrado.

Se ejecutan secuencialmente, sin pytest-xdist, estos módulos obligatorios:

- `tests/test_concurrencia_turnos_postgresql.py`
- `tests/test_appointment_reminders_postgresql.py`
- `tests/test_appointment_actions_postgresql.py`

`tests/test_pagos_postgresql.py` queda excluido porque requiere una variable
adicional no incluida en el contrato de esta fase, aunque sus SDK estén
mockeados. JUnit XML y una comprobación posterior fallan si cualquiera de los
tres módulos obligatorios no ejecuta al menos un test real.

## Variables y seguridad

El job define sólo variables sintéticas locales para la base PostgreSQL,
`DATABASE_URL`, `TEST_DATABASE_URL`, las tres URLs específicas de los módulos
obligatorios y `JWT_SECRET_KEY`. No se imprimen URLs completas ni contraseñas.

## Riesgos y rollback

La cobertura es selectiva y comparte una base efímera en ejecución secuencial;
no sustituye una validación productiva ni PostgreSQL CI requerido. Para
rollback se elimina únicamente el job PostgreSQL CI y su documentación, sin
alterar `Backend CI`, `Frontend CI`, Ruleset, producción o E2E.

## Branch Protection futura

No se modifica el Ruleset. Sólo después de una ejecución remota verde y una
revisión aprobatoria se evaluará convertir `PostgreSQL CI` en required.

## Criterios de aceptación

- [ ] YAML válido y diff limpio.
- [ ] Job `PostgreSQL CI` separado y no required.
- [ ] PostgreSQL 17-alpine saludable.
- [ ] Alembic heads, upgrade y current correctos.
- [ ] Tres módulos obligatorios ejecutados sin skips silenciosos.
- [ ] Ejecución remota verde y evidencia registrada.
- [ ] Documentación actualizada sin marcar la fase como completada.

## Progreso

- [x] Pre-check y selección de módulos.
- [x] Job y service container implementados.
- [x] Verificación JUnit contra skips silenciosos implementada.
- [x] Corrección preparada para conservar el esquema PostgreSQL migrado y
  verificar el exclusion constraint antes de pytest.
- [x] Parser JUnit corregido para usar atributos disponibles (`file`,
  `classname` y `name`) sin depender sólo de `file`.
- [ ] Validación local de sintaxis.
- [ ] Commit y push.
- [ ] Validación remota.

## Primer run remoto

El run `32597104272` confirmó que el service container y Alembic funcionaban:
`alembic heads`, `upgrade head` y `current` fueron correctos. Pytest recopiló
23 tests y produjo `21 passed, 2 failed, 1 warning`. Los dos fallos de
concurrencia dependían del constraint PostgreSQL creado por Alembic, que el
fixture global de `tests/conftest.py` podía eliminar mediante
`create_all/drop_all`. Además, el primer parser JUnit reportó falsamente los
tres módulos como no ejecutados al depender exclusivamente del atributo
`file`.

La corrección conserva el esquema migrado cuando `TEST_DATABASE_URL` usa
PostgreSQL, mantiene intacto el ciclo SQLite y verifica el constraint antes de
pytest. La nueva ejecución remota queda pendiente; la fase no está
completada.
