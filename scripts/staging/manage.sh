#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.staging.yml"
: "${STAGING_ENV_FILE:?Definí STAGING_ENV_FILE con la ruta privada fuera del repositorio}"

compose() {
  docker compose --project-name turnelia-staging --env-file "$STAGING_ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

python3 "$ROOT_DIR/scripts/staging/validate_compose.py" --env-file "$STAGING_ENV_FILE"

case "${1:-}" in
  validate)
    ;;
  up)
    compose up -d db api frontend
    ;;
  update)
    tag="${STAGING_IMAGE_TAG:-$(git -C "$ROOT_DIR" rev-parse --short HEAD)}"
    export STAGING_IMAGE_TAG="$tag"
    compose build api frontend
    compose up -d db api frontend
    ;;
  rollback)
    tag="${STAGING_IMAGE_TAG:?Indicá STAGING_IMAGE_TAG con una versión staging previamente validada}"
    for image in "turnelia-staging-api:$tag" "turnelia-staging-frontend:$tag"; do
      docker image inspect "$image" >/dev/null || {
        echo "No existe la imagen local previamente validada: $image" >&2
        exit 2
      }
    done
    export STAGING_IMAGE_TAG="$tag"
    compose up -d --no-build db api frontend
    ;;
  ps)
    compose ps
    ;;
  health)
    compose ps
    curl --fail --silent --show-error http://127.0.0.1:18081/health/ready
    printf '\n'
    curl --fail --silent --show-error --dump-header - http://127.0.0.1:18080/robots.txt
    ;;
  logs)
    compose logs --tail=100 api frontend db
    ;;
  stop)
    compose stop api frontend db
    ;;
  remove)
    if [[ "${STAGING_REMOVE_CONFIRM:-}" != "turnelia-staging" ]]; then
      echo "Para borrar sólo el staging aislado, exportá STAGING_REMOVE_CONFIRM=turnelia-staging." >&2
      exit 2
    fi
    python3 "$ROOT_DIR/scripts/staging/validate_resources.py"
    compose down --volumes --remove-orphans
    ;;
  *)
    echo "Uso: $0 validate|up|update|rollback|ps|health|logs|stop|remove" >&2
    exit 2
    ;;
esac
