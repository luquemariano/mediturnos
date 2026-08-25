# Exec Plan: protección de `main`

Estado: COMPLETADO

## Objetivo

Aplicar y verificar una protección mínima de `main` mediante GitHub Rulesets,
sin fusionar `feature/mvp` ni modificar código funcional, tests o workflows.

## Pre-check

- Repositorio: `luquemariano/mediturnos`.
- Rama por defecto: `main`.
- Visibilidad: pública.
- Permiso del operador: administrador.
- Protección clásica existente: no.
- Rulesets existentes: ninguno.
- Checks observados en la ejecución CI remota: `Backend CI` y `Frontend CI`,
  ambos provistos por GitHub Actions.

## Mecanismo elegido

Ruleset de repositorio, dirigido únicamente a `refs/heads/main`, con
enforcement `active`. Reglas previstas: Pull Request, checks requeridos
`Backend CI` y `Frontend CI`, bloqueo de force-push y bloqueo de eliminación.
No se requieren aprobaciones, actualización estricta de la rama, CODEOWNERS,
commits firmados, historial lineal ni gates de deployment.

El actor administrador tendrá bypass únicamente dentro de Pull Requests,
manteniendo el requisito normal de PR para los cambios ordinarios.

## Fallback y rollback

Si Rulesets no estuviera disponible o no pudiera expresar el contrato exacto,
se detendrá la implementación y se evaluará protección clásica sin ampliar el
alcance. El rollback autorizado consiste en eliminar exclusivamente el
Ruleset creado, después de verificar su identificador y alcance.

## Validación y aceptación

1. Verificar la configuración efectiva del Ruleset mediante GitHub.
2. Crear PRs descartables desde `main` y desde `feature/mvp`, sin fusionarlos.
3. Confirmar checks requeridos, mergeabilidad, bloqueo y camino verde.
4. Cerrar los PRs y eliminar únicamente sus ramas de prueba.
5. Confirmar que `main` y `feature/mvp` permanecen sin cambios ajenos.

## Riesgos y fuera de alcance

PostgreSQL CI, Playwright en GitHub Actions, branch protection avanzada,
producción, despliegues y cambios de código quedan fuera de esta fase.

## Progreso

- [x] Pre-check local y remoto.
- [x] Crear y verificar Ruleset `Turnelia main protection` (ID `21208601`).
- [x] Ejecutar PR descartable #2 desde `test/branch-protection`; checks
  `Backend CI` y `Frontend CI` quedaron bloqueantes y el PR terminó
  `MERGEABLE` pero `BLOCKED`, sin merge.
- [x] Limpiar rama y PR de prueba; `main` permaneció en `8f10b983` y el
  documento temporal no existe en `main`.
- [x] Actualizar documentación canónica.
- [x] Revisión final documental preparada.

### Validación verde adicional

- [x] PR #3 creado desde `test/branch-protection-green`, con head
  `ec6522f` y base `main` `8f10b983`.
- [x] Run `32595185386` ejecutado por `pull_request`.
- [x] `Backend CI` y `Frontend CI` terminaron en `success`.
- [x] El PR terminó `CLEAN`/`MERGEABLE` sin utilizar bypass y fue cerrado sin
  merge.
- [x] La rama temporal fue eliminada; `main` y `feature/mvp` permanecieron
  sin cambios.

## Resultado observado

El Ruleset quedó activo y se verificó mediante la API de GitHub. El PR #2
demostró que los checks requeridos se aplican: backend falló con dos tests del
`main` antiguo que recibieron `401` en lugar de los estados esperados, y
frontend falló porque ese `main` no contiene tests locales y `npx` intentó
resolver Vitest. Estos fallos pertenecen al estado histórico de `main`, no
son defectos introducidos por la protección y no se corrigieron en esta fase.

## Estado y límites

La Fase 5 está **COMPLETADA**. El Ruleset real es `Turnelia main protection`
(ID `21208601`), dirigido a `main`, con PR obligatorio, `Backend CI` y
`Frontend CI` requeridos, 0 approvals, `up-to-date` OFF, bypass
`pull_request`, y force-push/delete bloqueados. El fallback Classic está
documentado abajo. Los PR #2 y #3 validaron respectivamente el bloqueo rojo y
el camino verde; ambos fueron cerrados sin merge y sin bypass en la prueba
verde. `main` quedó sin commits de prueba.

## Recuperación de Ruleset

1. Abrir **Settings**.
2. Entrar en **Rulesets**.
3. Abrir `Turnelia main protection`.
4. Cambiar temporalmente `enforcement` a **Disabled**.
5. Corregir la configuración incorrecta.
6. Reactivar el Ruleset.
7. Repetir una prueba controlada.
8. Registrar la incidencia.

No usar force-push como recuperación normal.

## Recuperación Classic (fallback)

1. Abrir **Settings**.
2. Entrar en **Branch Protection**.
3. Editar o desactivar temporalmente la regla de `main`.
4. Corregir required checks y restricciones.
5. Reactivar la protección.
6. Repetir la validación.

Classic puede tener diferencias respecto del bypass limitado a Pull Requests
del Ruleset elegido.

## Criterios de aceptación

- [x] `main` protegida y PR obligatorio.
- [x] `Backend CI` y `Frontend CI` requeridos.
- [x] Approvals = 0 y push directo normal bloqueado.
- [x] Force-push y delete bloqueados.
- [x] Bypass y recuperación documentados.
- [x] PR #2 rojo y PR #3 verde validados.
- [x] Ambos PR cerrados sin merge y `main` sin commits de prueba.
- [x] Documentación actualizada.
