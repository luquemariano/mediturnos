from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path


def encontrar_duplicados(path: Path) -> dict[str, list[int]]:
    apariciones: dict[str, list[int]] = defaultdict(list)

    for numero_linea, linea in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        texto = linea.strip()

        if not texto or texto.startswith("#"):
            continue

        if "=" not in texto:
            continue

        clave = texto.split("=", 1)[0].strip()

        if clave:
            apariciones[clave].append(numero_linea)

    return {
        clave: lineas
        for clave, lineas in apariciones.items()
        if len(lineas) > 1
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detecta variables duplicadas en archivos .env.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Uno o más archivos .env a validar.",
    )
    args = parser.parse_args()

    hubo_errores = False

    for archivo in args.files:
        path = Path(archivo)

        if not path.exists():
            print(f"[ERROR] No existe: {path}")
            hubo_errores = True
            continue

        duplicados = encontrar_duplicados(path)

        if not duplicados:
            print(f"[OK] Sin variables duplicadas: {path}")
            continue

        hubo_errores = True
        print(f"[ERROR] Variables duplicadas en: {path}")

        for clave, lineas in sorted(duplicados.items()):
            numeros = ", ".join(str(numero) for numero in lineas)
            print(f"  - {clave}: líneas {numeros}")

    return 1 if hubo_errores else 0


if __name__ == "__main__":
    sys.exit(main())