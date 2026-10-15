"""Fail-closed ownership check before removing the staging Compose project."""

import json
import subprocess
import sys


PROJECT = "turnelia-staging"
EXPECTED_SERVICES = {"db", "api", "frontend"}
EXPECTED_VOLUMES = {"postgres_data", "staging_backups"}
EXPECTED_NETWORKS = {"backend", "ingress"}
EXPECTED_VOLUME_NAMES = {"postgres_data": "turnelia-staging-postgres", "staging_backups": "turnelia-staging-backups"}
EXPECTED_NETWORK_NAMES = {"backend": "turnelia-staging-backend", "ingress": "turnelia-staging-ingress"}


def inspect(kind: str, identifiers: list[str]) -> list[dict]:
    if not identifiers:
        return []
    result = subprocess.run(
        ["docker", kind, "inspect", *identifiers], capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise ValueError(f"No se pudieron verificar recursos Docker {kind} antes de remover staging.")
    return json.loads(result.stdout)


def verify() -> None:
    containers_result = subprocess.run(
        ["docker", "ps", "-aq", "--filter", f"label=com.docker.compose.project={PROJECT}"],
        capture_output=True,
        text=True,
        check=True,
    )
    containers = inspect("container", containers_result.stdout.split())
    services = set()
    for item in containers:
        labels = item.get("Config", {}).get("Labels") or {}
        if labels.get("com.turnelia.environment") != "staging" or labels.get("com.docker.compose.project") != PROJECT:
            raise ValueError("Se encontró un contenedor del proyecto sin propiedad staging verificable.")
        services.add(labels.get("com.docker.compose.service"))
    if services - EXPECTED_SERVICES:
        raise ValueError("Se encontró un servicio Docker inesperado; no se removió ningún recurso.")

    volume_result = subprocess.run(
        ["docker", "volume", "ls", "-q", "--filter", f"label=com.docker.compose.project={PROJECT}"],
        capture_output=True,
        text=True,
        check=True,
    )
    volumes = inspect("volume", volume_result.stdout.split())
    volume_keys = set()
    for item in volumes:
        labels = item.get("Labels") or {}
        if labels.get("com.docker.compose.project") != PROJECT:
            raise ValueError("Se encontró un volumen sin propiedad staging verificable.")
        key = labels.get("com.docker.compose.volume")
        if EXPECTED_VOLUME_NAMES.get(key) != item.get("Name"):
            raise ValueError("Se encontró un volumen con nombre distinto al staging aprobado.")
        volume_keys.add(key)
    if volume_keys - EXPECTED_VOLUMES:
        raise ValueError("Se encontró un volumen inesperado; no se removió ningún recurso.")

    network_result = subprocess.run(
        ["docker", "network", "ls", "-q", "--filter", f"label=com.docker.compose.project={PROJECT}"],
        capture_output=True,
        text=True,
        check=True,
    )
    networks = inspect("network", network_result.stdout.split())
    network_keys = set()
    for item in networks:
        labels = item.get("Labels") or {}
        if labels.get("com.docker.compose.project") != PROJECT:
            raise ValueError("Se encontró una red sin propiedad staging verificable.")
        key = labels.get("com.docker.compose.network")
        if EXPECTED_NETWORK_NAMES.get(key) != item.get("Name"):
            raise ValueError("Se encontró una red con nombre distinto al staging aprobado.")
        network_keys.add(key)
    if network_keys - EXPECTED_NETWORKS:
        raise ValueError("Se encontró una red inesperada; no se removió ningún recurso.")


if __name__ == "__main__":
    try:
        verify()
    except (ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print(f"Limpieza staging rechazada: {error}", file=sys.stderr)
        raise SystemExit(1)
    print("[OK] Todos los recursos Docker del proyecto están etiquetados como staging y usan nombres permitidos.")
