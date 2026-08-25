# Exec Plans activos

Un Exec Plan describe trabajo complejo todavía activo y conserva contexto, decisiones, alcance y validación entre análisis, implementación y revisión.

## Cuándo crear uno

Cuando una tarea tenga varias etapas, riesgos cruzados, cambios en varios módulos o coordinación Builder → Reviewer. No es necesario para cambios triviales.

## Plantilla sugerida

```markdown
# [Título]
## Objetivo
## Contexto
## Alcance
## Fuera de alcance
## Arquitectura afectada
## Permisos y seguridad
## Modelo de datos
## Frontend
## Backend
## Tests
## Migraciones
## Riesgos
## Pasos
## Validación
## Documentación
## Criterio de finalización
```

Mientras esté activo debe reflejar decisiones, bloqueos, validaciones y próximos pasos. No se crean aquí planes concretos de features durante esta fase.
