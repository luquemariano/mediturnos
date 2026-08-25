import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.database.connection import obtener_db
from app.main import app, crear_app


JWT_SEGURO = "clave-segura-produccion-32-caracteres-minimo"
DATABASE_POSTGRES = (
    "postgresql+psycopg://usuario:password@db/mediturnos"
)


def crear_configuracion_produccion(**cambios) -> Settings:
    valores = {
        "app_env": "production",
        "database_url": DATABASE_POSTGRES,
        "jwt_secret_key": JWT_SEGURO,
        "cors_allowed_origins": ["https://app.mediturnos.example"],
        "frontend_url": "https://app.mediturnos.example",
        "email_provider": "resend",
        "resend_api_key": "resend-test-key",
        "email_from": "Turnelia <no-reply@mediturnos.example>",
    }
    valores.update(cambios)

    return Settings(_env_file=None, **valores)


def test_health_live_no_depende_de_base(client):
    respuesta = client.get("/health/live")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_health_ready_con_base_disponible(client):
    respuesta = client.get("/health/ready")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_health_ready_con_base_no_disponible(client):
    dependencia_original = app.dependency_overrides[obtener_db]

    class SesionNoDisponible:
        def execute(self, consulta):
            raise RuntimeError("detalle interno sensible")

    def obtener_db_no_disponible():
        yield SesionNoDisponible()

    app.dependency_overrides[obtener_db] = (
        obtener_db_no_disponible
    )

    try:
        respuesta = client.get("/health/ready")
    finally:
        app.dependency_overrides[obtener_db] = (
            dependencia_original
        )

    assert respuesta.status_code == 503
    assert respuesta.json() == {
        "detail": "Base de datos no disponible."
    }
    assert "sensible" not in respuesta.text


@pytest.mark.parametrize(
    "ambiente",
    ["development", "demo", "test"],
)
def test_documentacion_disponible_fuera_de_produccion(
    ambiente,
):
    configuracion = Settings(
        _env_file=None,
        app_env=ambiente,
        jwt_secret_key="test-secret",
    )

    with TestClient(crear_app(configuracion)) as cliente:
        assert cliente.get("/docs").status_code == 200
        assert cliente.get("/redoc").status_code == 200
        assert cliente.get("/openapi.json").status_code == 200


def test_documentacion_deshabilitada_en_produccion():
    with TestClient(
        crear_app(crear_configuracion_produccion())
    ) as cliente:
        assert cliente.get("/docs").status_code == 404
        assert cliente.get("/redoc").status_code == 404
        assert cliente.get("/openapi.json").status_code == 404


def test_produccion_rechaza_sqlite():
    with pytest.raises(
        ValidationError,
        match="SQLite no está permitido",
    ):
        crear_configuracion_produccion(
            database_url="sqlite:///./mediturnos.db",
        )


def test_produccion_normaliza_url_postgresql_sin_driver():
    configuracion = crear_configuracion_produccion(
        database_url=(
            "postgresql://usuario:password@db/mediturnos"
        ),
    )

    assert configuracion.database_url.startswith(
        "postgresql+psycopg://"
    )


def test_produccion_rechaza_driver_postgresql_incompatible():
    with pytest.raises(
        ValidationError,
        match="compatible con psycopg",
    ):
        crear_configuracion_produccion(
            database_url=(
                "postgresql+asyncpg://usuario:password@db/mediturnos"
            ),
        )


def test_error_productivo_no_expone_valores_sensibles():
    secreto = "SUPER-SECRETO-QUE-NO-DEBE-MOSTRARSE"
    url_con_password = "sqlite:///password-muy-sensible.db"

    with pytest.raises(ValidationError) as error:
        crear_configuracion_produccion(
            database_url=url_con_password,
            jwt_secret_key=secreto,
        )

    mensaje = str(error.value)

    assert secreto not in mensaje
    assert url_con_password not in mensaje


@pytest.mark.parametrize(
    "secreto",
    [
        "reemplazar_por_una_clave_larga_y_aleatoria",
        "demasiado-corta",
        " " * 32,
    ],
)
def test_produccion_rechaza_jwt_inseguro(secreto):
    with pytest.raises(
        ValidationError,
        match="al menos 32 caracteres",
    ):
        crear_configuracion_produccion(
            jwt_secret_key=secreto,
        )


@pytest.mark.parametrize(
    "origen",
    [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.2:5173",
        "http://[::1]:5173",
        "http://[::ffff:127.0.0.2]:5173",
        "http://localhost.:5173",
    ],
)
def test_produccion_rechaza_cors_local(origen):
    with pytest.raises(
        ValidationError,
        match="no puede contener localhost",
    ):
        crear_configuracion_produccion(
            cors_allowed_origins=[origen],
        )


def test_produccion_acepta_cors_https_publico():
    configuracion = crear_configuracion_produccion(
        cors_allowed_origins=[
            "https://app.mediturnos.example",
        ],
    )

    assert configuracion.cors_allowed_origins == [
        "https://app.mediturnos.example",
    ]


@pytest.mark.parametrize(
    ("cambios", "mensaje"),
    [
        ({"email_provider": "in_memory"}, "EMAIL_PROVIDER"),
        ({"resend_api_key": None}, "RESEND_API_KEY"),
        ({"email_from": None}, "EMAIL_FROM"),
        ({"frontend_url": "http://localhost:5173"}, "FRONTEND_URL"),
    ],
)
def test_produccion_exige_email_transaccional_configurado(cambios, mensaje):
    with pytest.raises(ValidationError, match=mensaje):
        crear_configuracion_produccion(**cambios)
