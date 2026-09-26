# Flujo autónomo de trabajo — Turnelia

Este documento define cómo un agente puede llevar una tarea desde el roadmap hasta producción con mínima intervención humana.

## Activación

El flujo autónomo se considera autorizado cuando el usuario pide explícitamente ejecutar una tarea, fase o ítem del roadmap **siguiendo el flujo autónomo** o una instrucción equivalente.

Si esa autorización no existe, aplicar las reglas conservadoras de `AGENTS.md` y no hacer commit, push, merge ni deploy por cuenta propia.

## Objetivo

La secuencia esperada es:

```text
requisito
→ análisis
→ implementación
→ tests
→ autocorrección
→ commit
→ push
→ PR
→ CI
→ revisión final
→ merge
→ deploy
→ verificación
→ informe final
```

El agente no debe detenerse entre pasos rutinarios si puede continuar de forma segura.

## 1. Preflight

Antes de modificar nada:

- leer `AGENTS.md`, `docs/ROADMAP.md`, `docs/CURRENT_STATE.md` y la documentación específica de la tarea;
- revisar `docs/DEPLOYMENT.md` antes de cualquier operación productiva;
- confirmar rama activa, `git status`, sincronización con remoto y PR existente si la hubiera;
- preservar cambios ajenos y archivos no relacionados;
- no asumir que documentación histórica refleja la operación actual si el código, la configuración o documentación verificada indican otra cosa.

## 2. Alcance y planificación

- implementar el cambio mínimo que satisfaga la tarea;
- revisar impacto en backend, frontend, persistencia, migraciones, workers, seguridad, permisos, analytics, documentación, landing y Centro de Ayuda;
- no ampliar el alcance sin necesidad;
- si falta una decisión funcional real, detenerse y preguntar;
- resolver decisiones puramente técnicas sin pedir permiso cuando haya una opción segura y coherente con el proyecto.

## 3. Branching

Para nuevas tareas:

- partir de `main` actualizado, salvo que corresponda continuar una rama activa ya existente;
- usar ramas descriptivas como `feature/...`, `fix/...`, `chore/...` o `docs/...`;
- no desarrollar directamente sobre `main`.

## 4. Implementación

Respetar la arquitectura y convenciones existentes.

Reglas obligatorias:

- no exponer secretos, tokens, credenciales ni datos sensibles;
- usar Alembic para cambios persistentes;
- mantener compatibilidad PostgreSQL;
- mantener autorización y ownership;
- evitar nuevas dependencias salvo justificación clara;
- no introducir soluciones temporales cuando exista una solución correcta razonable.

## 5. Validación

Agregar o actualizar tests proporcionales al cambio.

Usar los comandos vigentes del repositorio, incluyendo cuando corresponda:

- pytest;
- Vitest;
- lint;
- build;
- Playwright E2E;
- `verify.ps1`.

Ejecutar siempre:

```text
git diff --check
```

Revisar el diff completo antes del commit.

## 6. Autocorrección

Si un test, build, lint o CI falla:

1. investigar causa raíz;
2. reproducir cuando sea posible;
3. distinguir entre regresión real, fixture, dependencia temporal, infraestructura, configuración o problema externo;
4. corregir automáticamente si la solución es pequeña, segura y técnicamente clara;
5. repetir validaciones.

No cambiar reglas de negocio solo para hacer pasar un test. No silenciar tests sin demostrar la causa.

## 7. Documentación de producto

Toda nueva funcionalidad visible para usuarios debe evaluar si corresponde actualizar:

- landing pública;
- Centro de Ayuda;
- roadmap y estado actual.

No marcar una funcionalidad como disponible públicamente antes del deploy.

## 8. Commit, push y PR

Cuando el cambio esté validado:

- revisar `git status` y diff;
- evitar archivos accidentales, temporales, dumps, secretos y `.env`;
- crear commits coherentes;
- hacer push;
- crear o actualizar la PR hacia `main`;
- documentar resumen, tests, migraciones, implicancias operativas y pendientes reales.

## 9. CI

Esperar los checks relevantes de GitHub Actions.

Si fallan, iterar:

```text
corrección → test → commit → push → CI
```

hasta obtener CI verde o encontrar un bloqueo que requiera intervención humana.

## 10. Revisión pre-merge

Antes del merge confirmar:

- CI verde;
- sin conflictos;
- cambios dentro del alcance;
- sin secretos;
- migraciones revisadas;
- documentación necesaria actualizada;
- sin riesgos conocidos no resueltos.

## 11. Merge

Con todos los criterios cumplidos, el agente puede mergear usando el método habitual del repositorio.

Después:

- cambiar a `main`;
- sincronizar con `origin/main`;
- confirmar working tree limpio;
- registrar el SHA candidato a producción.

## 12. Deploy

Seguir únicamente el procedimiento vigente en `docs/DEPLOYMENT.md` y documentación operativa relacionada.

Antes de modificar producción:

- confirmar host y directorio correctos;
- revisar estado actual;
- confirmar servicios y espacio disponible cuando sea relevante;
- comprobar si hay migraciones;
- no alterar secretos, firewall, DNS ni ACL salvo que la tarea lo requiera explícitamente.

No borrar volúmenes productivos, no reinicializar la base y no ejecutar seeds de desarrollo.

## 13. Verificación post-deploy

No considerar exitoso un deploy solo porque los contenedores iniciaron.

Verificar según el alcance:

- `docker compose ps`;
- health/readiness de API;
- frontend HTTP;
- logs recientes;
- servicios o workers afectados;
- migraciones;
- endpoints relevantes;
- smoke tests de la funcionalidad;
- correspondencia entre código desplegado y SHA de `main`.

## 14. Rollback

Si producción queda degradada:

- detener la propagación del problema;
- recopilar evidencia;
- usar un rollback seguro si está claramente definido;
- volver a verificar servicios.

Si el rollback puede afectar datos o una migración es irreversible, detenerse antes y pedir intervención.

## 15. Cuándo pedir intervención humana

Detenerse solo ante alguno de estos casos:

- login interactivo, MFA, CAPTCHA u OAuth que requiera consentimiento;
- credenciales inexistentes;
- decisión funcional ambigua;
- posible pérdida de datos;
- migración destructiva;
- costo económico no autorizado;
- cambio significativo de infraestructura o seguridad;
- conflicto con trabajo ajeno;
- secreto requerido no disponible;
- rollback con riesgo de datos.

Al detenerse, informar claramente qué ocurrió, qué se necesita y qué paso seguirá después.

## 16. Informe final

Entregar un único resumen con:

- estado: completada, bloqueada o rollback;
- implementación realizada;
- rama, commits, PR, merge y SHA final;
- tests, lint, build y CI;
- estado del deploy;
- health y smoke tests;
- documentación actualizada;
- pendientes reales.

No listar cada comando ejecutado salvo que sea relevante para diagnóstico.

## Ejemplos de uso

```text
Ejecutá F12.1 completa siguiendo el flujo autónomo del proyecto.
```

```text
Implementá la próxima fase pendiente del roadmap y llevala hasta producción siguiendo el flujo autónomo.
```

```text
Corregí este bug siguiendo el flujo autónomo. Detenete solo si aparece uno de los bloqueos definidos.
```
