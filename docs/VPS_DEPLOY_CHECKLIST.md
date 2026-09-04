# Turnelia VPS Deploy Checklist

Checklist operativo para despliegues y cambios de configuración en el VPS de Turnelia.

## 1. Antes de desplegar

Trabajar siempre desde una rama `feature/` o `chore/` y verificar:

```bash
git status
git branch --show-current
git pull --ff-only