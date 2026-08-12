import pytest

from app.scripts import start


def test_puerto_usa_8000_por_defecto(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)

    assert start.obtener_puerto() == "8000"


@pytest.mark.parametrize("valor", ["0", "65536", "abc"])
def test_puerto_rechaza_valores_invalidos(monkeypatch, valor):
    monkeypatch.setenv("PORT", valor)

    with pytest.raises(RuntimeError, match="PORT debe ser"):
        start.obtener_puerto()


def test_arranque_migra_antes_de_iniciar_uvicorn(monkeypatch):
    eventos = []
    monkeypatch.setenv("PORT", "9000")

    def ejecutar_migracion(comando, check):
        eventos.append(("migracion", comando, check))

    def ejecutar_uvicorn(programa, argumentos):
        eventos.append(("uvicorn", programa, argumentos))

    monkeypatch.setattr(start.subprocess, "run", ejecutar_migracion)
    monkeypatch.setattr(start.os, "execvp", ejecutar_uvicorn)

    start.main()

    assert eventos == [
        (
            "migracion",
            ["alembic", "upgrade", "head"],
            True,
        ),
        (
            "uvicorn",
            "uvicorn",
            [
                "uvicorn",
                "app.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "9000",
            ],
        ),
    ]


def test_arranque_no_inicia_uvicorn_si_alembic_falla(
    monkeypatch,
):
    uvicorn_ejecutado = False

    def migracion_fallida(comando, check):
        assert comando == ["alembic", "upgrade", "head"]
        assert check is True
        raise start.subprocess.CalledProcessError(
            returncode=1,
            cmd=comando,
        )

    def ejecutar_uvicorn(programa, argumentos):
        nonlocal uvicorn_ejecutado
        uvicorn_ejecutado = True

    monkeypatch.setattr(
        start.subprocess,
        "run",
        migracion_fallida,
    )
    monkeypatch.setattr(start.os, "execvp", ejecutar_uvicorn)

    with pytest.raises(start.subprocess.CalledProcessError):
        start.main()

    assert uvicorn_ejecutado is False
