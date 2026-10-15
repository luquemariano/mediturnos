"""Fail-closed validation of the resolved staging Compose topology."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPOSE = ROOT / "docker-compose.staging.yml"


def validar(env_file: Path) -> None:
    environment = os.environ.copy()
    environment["STAGING_ENV_FILE"] = str(env_file.resolve())
    result = subprocess.run(
        ["docker", "compose", "--project-name", "turnelia-staging", "--env-file", str(env_file.resolve()), "-f", str(COMPOSE), "config", "--format", "json"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError("Docker Compose no pudo validar la configuración privada de staging.")
    config = json.loads(result.stdout)
    if config.get("name") != "turnelia-staging":
        raise ValueError("El nombre de proyecto Compose no coincide con staging.")
    services = config.get("services", {})
    if set(services) != {"db", "api", "frontend"}:
        raise ValueError("Staging contiene servicios fuera de la lista permitida.")
    if any("container_name" in service for service in services.values()):
        raise ValueError("Staging no puede fijar nombres de contenedor globales.")
    db, api, frontend = services["db"], services["api"], services["frontend"]
    if db.get("ports") or set(db.get("networks", {})) != {"backend"}:
        raise ValueError("PostgreSQL debe permanecer privado en la red backend staging.")
    networks = config.get("networks", {})
    backend = networks.get("backend", {})
    ingress = networks.get("ingress", {})
    if backend.get("name") != "turnelia-staging-backend" or ingress.get("name") != "turnelia-staging-ingress" or not backend.get("internal") or backend.get("external") or ingress.get("external"):
        raise ValueError("Las redes staging deben ser propias y la red backend interna.")
    if set(api.get("networks", {})) != {"backend", "ingress"}:
        raise ValueError("La API debe usar sólo las redes aisladas de staging.")
    if set(frontend.get("networks", {})) != {"ingress"}:
        raise ValueError("El frontend debe usar sólo la red ingress staging.")
    ports = {
        service: {(port.get("host_ip"), int(port.get("published")), int(port.get("target"))) for port in config["services"][service].get("ports", [])}
        for service in ("api", "frontend")
    }
    for service, expected in (("api", {("127.0.0.1", 18081, 8000)}), ("frontend", {("127.0.0.1", 18080, 80)})):
        if ports[service] != expected:
            raise ValueError("Los puertos publicados deben limitarse a loopback 18080/18081.")
    database = api.get("environment", {}).get("DATABASE_URL", "")
    if "@db:5432/turnelia_staging" not in database:
        raise ValueError("La API no apunta a la base PostgreSQL staging esperada.")
    if api.get("environment", {}).get("APP_ENV") != "staging":
        raise ValueError("APP_ENV debe ser staging.")
    api_environment = api.get("environment", {})
    whatsapp_enabled = api_environment.get("WHATSAPP_ENABLED") in {True, "true"}
    meta_enabled = api_environment.get("STAGING_WHATSAPP_META_ENABLED") in {True, "true"}
    meta_confirmed = api_environment.get("STAGING_WHATSAPP_META_TEST_NUMBER_CONFIRMED") in {True, "true"}
    whatsapp_provider = api_environment.get("WHATSAPP_PROVIDER")
    if whatsapp_enabled:
        if not meta_enabled or not meta_confirmed or whatsapp_provider != "meta":
            raise ValueError("WhatsApp Meta sólo se habilita con bandera explícita, IDs/app de prueba confirmados y proveedor meta.")
        if api_environment.get("PUBLIC_API_URL") != "https://api.staging.turnelia.com.ar":
            raise ValueError("WhatsApp Meta requiere el webhook HTTPS dedicado de staging.")
    elif whatsapp_provider != "fake" or meta_enabled:
        raise ValueError("WhatsApp staging debe permanecer deshabilitado/fake salvo configuración Meta explícita.")
    args = frontend.get("build", {}).get("args", {})
    if args.get("VITE_ANALYTICS_ENABLED") not in {False, "false"} or args.get("VITE_POSTHOG_PROJECT_TOKEN"):
        raise ValueError("El frontend staging no debe incluir analítica.")
    if any(volume.get("external") for volume in config.get("volumes", {}).values()):
        raise ValueError("Los volúmenes staging deben ser propios.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        validar(args.env_file)
    except ValueError as error:
        print(f"Configuración de staging rechazada: {error}", file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError):
        print("Configuración de staging rechazada; revisá la ruta privada y la salida de Docker Compose sin revelar variables.", file=sys.stderr)
        return 1
    print("[OK] Compose staging aislado: DB privada, redes/volúmenes dedicados, loopback, noindex y WhatsApp fake o Meta de prueba allowlisted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
