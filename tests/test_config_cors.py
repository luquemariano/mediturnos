import pytest
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from pydantic_settings import SettingsError

from app.core.config import Settings
from app.main import app


def crear_configuracion_desde_entorno(
    monkeypatch,
    valor: str,
) -> Settings:
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", valor)

    return Settings(
        _env_file=None,
        jwt_secret_key="test-secret",
    )


def test_cors_usa_origenes_de_desarrollo_por_defecto():
    configuracion = Settings(
        _env_file=None,
        jwt_secret_key="test-secret",
    )

    assert configuracion.cors_allowed_origins == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_cors_acepta_origen_https_de_produccion(monkeypatch):
    configuracion = crear_configuracion_desde_entorno(
        monkeypatch,
        '["https://app.mediturnos.example:8443"]',
    )

    assert configuracion.cors_allowed_origins == [
        "https://app.mediturnos.example:8443",
    ]


@pytest.mark.parametrize(
    ("valor", "mensaje"),
    [
        ("[]", "no puede ser una lista vacía"),
        ('["*"]', "no puede contener '*'"),
        (
            '["https://app.mediturnos.example/api"]',
            "no se permiten path, query ni fragment",
        ),
        (
            '["https://app.mediturnos.example?entorno=prod"]',
            "no se permiten path, query ni fragment",
        ),
        (
            '["https://app.mediturnos.example#inicio"]',
            "no se permiten path, query ni fragment",
        ),
        (
            '["https://usuario:clave@app.mediturnos.example"]',
            "solamente esquema, host y puerto opcional",
        ),
    ],
)
def test_cors_rechaza_origenes_invalidos(
    monkeypatch,
    valor,
    mensaje,
):
    with pytest.raises(ValidationError, match=mensaje):
        crear_configuracion_desde_entorno(
            monkeypatch,
            valor,
        )


def test_cors_rechaza_json_invalido(monkeypatch):
    with pytest.raises(
        SettingsError,
        match="cors_allowed_origins",
    ):
        crear_configuracion_desde_entorno(
            monkeypatch,
            "no-es-json",
        )


def test_cors_configura_metodos_y_headers_explicitos():
    middleware = next(
        middleware
        for middleware in app.user_middleware
        if middleware.cls is CORSMiddleware
    )

    assert middleware.kwargs["allow_credentials"] is True
    assert middleware.kwargs["allow_methods"] == [
        "GET",
        "POST",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ]
    assert middleware.kwargs["allow_headers"] == [
        "Authorization",
        "Content-Type",
    ]
