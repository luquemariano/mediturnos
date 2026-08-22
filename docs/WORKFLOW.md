# Workflow de trabajo con agentes

Complementa [`AGENTS.md`](../AGENTS.md).

```text
IDEA / NECESIDAD
→ análisis de producto
→ inspección del repositorio
→ plan de ejecución
→ implementación
→ tests
→ revisión
→ correcciones
→ verificación
→ commit/push sólo con autorización explícita
→ actualización de documentación
```

## Reglas

1. Leer `AGENTS.md` y la documentación relacionada.
2. Inspeccionar código, configuración, migraciones y tests.
3. Identificar permisos, ownership, compatibilidad y riesgos.
4. Planificar e implementar el cambio mínimo.
5. Ejecutar validaciones proporcionales al riesgo.
6. Revisar diff, estado Git y efectos colaterales.
7. Hacer commit/push sólo con autorización explícita.
8. Actualizar la memoria canónica cuando cambie un flujo o decisión.

**Una decisión importante que sólo existe en una conversación todavía no forma parte de la memoria canónica del proyecto.**

Las decisiones relevantes deben reflejarse, según corresponda, en código, tests, [`docs/DECISIONS.md`](DECISIONS.md), [`docs/CURRENT_STATE.md`](CURRENT_STATE.md) y documentación especializada como [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) o [`docs/PRODUCT.md`](PRODUCT.md).

Los trabajos complejos pueden documentarse en [`docs/exec-plans/active/`](exec-plans/active/) mientras están activos y moverse a [`docs/exec-plans/completed/`](exec-plans/completed/) al finalizar. Los planes completados de setup/verificación y Playwright/E2E sirven como ejemplos históricos: [`harness-setup-verification.md`](exec-plans/completed/harness-setup-verification.md) y [`playwright-e2e.md`](exec-plans/completed/playwright-e2e.md).

## Conceptos y prácticas del proceso

- **Exec Plans:** organización de tareas complejas, sin sustituir inspección ni autorización.
- **Builder:** práctica de implementación y validación con alcance explícito.
- **Reviewer:** revisión sistemática de cambios, permisos, tests y riesgos.
- Actualmente el flujo **Builder → Reviewer** se ejecuta manualmente; no se documenta como infraestructura automatizada.
- **Playwright/E2E:** cobertura local de flujos completos mediante `verify.ps1 -E2E`; Fase 3 completada.
- **Skills:** todavía no incorporadas como mecanismo específico del repositorio.
- **Multiagentes automatizados:** todavía no incorporados.
- **MCP:** todavía no incorporado.

Cuando una afirmación no pueda comprobarse desde el repositorio, debe marcarse `NO DETERMINADO`.
