import os
import subprocess


def obtener_puerto() -> str:
    valor = os.getenv("PORT", "8000")

    try:
        puerto = int(valor)
    except ValueError as error:
        raise RuntimeError(
            "PORT debe ser un número entero entre 1 y 65535."
        ) from error

    if not 1 <= puerto <= 65535:
        raise RuntimeError(
            "PORT debe ser un número entero entre 1 y 65535."
        )

    return str(puerto)


def main() -> None:
    puerto = obtener_puerto()
    subprocess.run(
        ["alembic", "upgrade", "head"],
        check=True,
    )
    os.execvp(
        "uvicorn",
        [
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            puerto,
        ],
    )


if __name__ == "__main__":
    main()
