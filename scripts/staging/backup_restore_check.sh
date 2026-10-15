#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.staging.yml"
: "${STAGING_ENV_FILE:?Definí STAGING_ENV_FILE con la ruta privada fuera del repositorio}"

compose() {
  docker compose --project-name turnelia-staging --env-file "$STAGING_ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

python "$ROOT_DIR/scripts/staging/validate_compose.py" --env-file "$STAGING_ENV_FILE"

case "${1:-}" in
  backup)
    compose exec -T db sh -ec '
      file="/var/backups/staging/${POSTGRES_DB}_$(date -u +%Y%m%dT%H%M%SZ).dump"
      pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$file"
      sha256sum "$file" > "$file.sha256"
      printf "Backup sintético staging creado y verificado: %s\n" "${file##*/}"
    '
    ;;
  restore-check)
    compose exec -T db sh -ec '
      file=$(ls -1t "/var/backups/staging/${POSTGRES_DB}_"*.dump 2>/dev/null | head -n 1 || true)
      test -n "$file"
      (cd /var/backups/staging && sha256sum -c "${file##*/}.sha256")
      restore_db="turnelia_staging_restore_$(date -u +%s)_$(od -An -N8 -tx1 /dev/urandom | tr -d \" \\n\")"
      restore_created=false
      drop_restore() { if [ "$restore_created" = true ]; then dropdb -U "$POSTGRES_USER" "$restore_db" >/dev/null; fi; }
      trap drop_restore EXIT
      createdb -U "$POSTGRES_USER" "$restore_db"
      restore_created=true
      pg_restore -U "$POSTGRES_USER" -d "$restore_db" --no-owner --no-privileges "$file"
      revision=$(psql -U "$POSTGRES_USER" -d "$restore_db" -Atc "SELECT version_num FROM alembic_version")
      test -n "$revision"
      printf "Restore sintética aislada correcta; revisión Alembic: %s\n" "$revision"
    '
    ;;
  *)
    echo "Uso: $0 backup|restore-check" >&2
    exit 2
    ;;
esac
