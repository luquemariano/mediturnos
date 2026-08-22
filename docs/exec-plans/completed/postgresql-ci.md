# Exec Plan: PostgreSQL CI

Estado: COMPLETADO

## Objetivo

Agregar un job separado de GitHub Actions que valide migraciones y flujos
PostgreSQL seleccionados sobre una base efímera de CI. PostgreSQL CI pasó a ser
required en Branch Protection después de la validación verde y la revisión.

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
no sustituye una validación productiva ni la versión productiva de PostgreSQL.
Para
rollback se elimina únicamente el job PostgreSQL CI y su documentación, sin
alterar `Backend CI`, `Frontend CI`, Ruleset, producción o E2E.

## Branch Protection

El Ruleset `Turnelia main protection` exige `Backend CI`, `Frontend CI` y
`PostgreSQL CI`. No se modificaron approvals, `up-to-date`, bypass,
force-push, deletion ni el target `main`.

## Criterios de aceptación

- [ ] YAML válido y diff limpio.
- [x] Job `PostgreSQL CI` separado y required.
- [ ] PostgreSQL 17-alpine saludable.
- [ ] Alembic heads, upgrade y current correctos.
- [ ] Tres módulos obligatorios ejecutados sin skips silenciosos.
- [x] Ejecución remota verde y evidencia registrada.
- [x] Documentación actualizada y fase completada.

## Progreso

- [x] Pre-check y selección de módulos.
- [x] Job y service container implementados.
- [x] Verificación JUnit contra skips silenciosos implementada.
- [x] Corrección preparada para conservar el esquema PostgreSQL migrado y
  verificar el exclusion constraint antes de pytest.
- [x] Parser JUnit corregido para usar atributos disponibles (`file`,
  `classname` y `name`) sin depender sólo de `file`.
- [x] Validación local de sintaxis y diff limpio.
- [x] Commit y push.
- [x] Validación remota verde en run `32597419679` sobre commit `c9746cb`.

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
pytest. La fase quedó completada tras integrar PostgreSQL CI en Branch
Protection.

La segunda ejecución remota (`32597419679`) confirmó PostgreSQL `17-alpine`,
Alembic correcto, el constraint `ex_turnos_profesional_intervalo_activo`
presente, `23 passed, 0 failed, 0 skipped` y el verificador JUnit satisfecho
para los tres módulos obligatorios. `Backend CI` terminó con `538 passed, 26
skipped, 2 warnings` y `Frontend CI` terminó correctamente. PostgreSQL CI
quedó required en Branch Protection.

## Validación de Branch Protection

El Ruleset ID `21208601` quedó con los tres required checks: `Backend CI`,
`Frontend CI` y `PostgreSQL CI`. El PR descartable #4, desde
`test/postgresql-ci-required` hacia `main`, usó base `8f10b983` y head temporal
`b97b9ed`. El run `32597812092` terminó con los tres jobs en `success`; el PR
terminó `CLEAN`/`MERGEABLE`, demostrando que los checks verdes permiten el
merge. No se utilizó bypass, no se hizo merge y la rama temporal fue
eliminada.

## Criterios finales

- [x] PostgreSQL CI requerido junto a Backend CI y Frontend CI.
- [x] Alembic, constraint, 23 tests y verificador JUnit validados.
- [x] PR required-checks verde y mergeable sin bypass.
- [x] PR cerrado sin merge; `main` sin cambios de prueba.
- [x] PostgreSQL productivo continúa NO DETERMINADO.
- [x] `tests/test_pagos_postgresql.py` permanece fuera de alcance.
