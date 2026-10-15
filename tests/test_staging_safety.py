import re

import pytest
from pydantic import SecretStr, ValidationError
from pathlib import Path
from tempfile import TemporaryDirectory

from app.core.config import Settings
from app.scripts import seed_staging
from scripts.staging.generate_env import create_env_file
from app.services.email_service import EmailDeliveryError, ResendEmailProvider, TransactionalEmail


def test_scripts_staging_invocan_python_con_version_explicita():
    scripts_dir = Path(__file__).resolve().parents[1] / "scripts" / "staging"
    unversioned_invocations = []

    for script in scripts_dir.glob("*.sh"):
        for line_number, line in enumerate(script.read_text(encoding="utf-8").splitlines(), start=1):
            command_text = line.split("#", maxsplit=1)[0]
            if re.search(r"(?<![A-Za-z0-9_./-])python\s+(?=[^\s])", command_text):
                unversioned_invocations.append(f"{script.name}:{line_number}")

    assert not unversioned_invocations, (
        "Los scripts de staging deben invocar Python como python3: "
        + ", ".join(unversioned_invocations)
    )


def staging_settings(**overrides):
    values = {
        "_env_file": None,
        "app_env": "staging",
        "jwt_secret_key": "synthetic-staging-jwt-secret-" + "x" * 32,
        "database_url": "postgresql+psycopg://staging:fake@db:5432/turnelia_staging",
        "frontend_url": "http://127.0.0.1:18080",
        "public_api_url": "http://127.0.0.1:18081",
        "cors_allowed_origins": ["http://127.0.0.1:18080"],
        "appointment_action_secret": SecretStr("a" * 40),
        "study_access_secret": SecretStr("b" * 40),
        "email_provider": "in_memory",
        "whatsapp_enabled": False,
        "whatsapp_provider": "fake",
        "mercadopago_env": "sandbox",
        "object_storage_provider": "fake",
    }
    values.update(overrides)
    return Settings(**values)


def test_staging_acepta_solo_base_y_urls_loopback_dedicadas():
    config = staging_settings()

    assert config.app_env == "staging"
    assert "turnelia_staging" in config.database_url


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("database_url", "postgresql+psycopg://x:y@prod-db:5432/turnelia_staging", "servicio aislado db"),
        ("database_url", "postgresql+psycopg://x:y@db:5432/turnelia", "base turnelia_staging"),
        ("database_url", "sqlite:///./turnelia_staging.db", "servicio aislado db"),
        ("frontend_url", "https://turnelia.com.ar", "subdominio staging dedicado"),
        ("public_api_url", "https://api.turnelia.com.ar", "subdominio staging dedicado"),
        ("cors_allowed_origins", ["https://turnelia.com.ar"], "dominios ajenos"),
        ("mercadopago_env", "production", "sandbox"),
        ("whatsapp_enabled", True, "deshabilitado con proveedor fake"),
        ("whatsapp_provider", "meta", "deshabilitado con proveedor fake"),
        ("email_provider", "resend", "EMAIL_PROVIDER debe ser in_memory"),
    ],
)
def test_staging_rechaza_configuracion_que_puede_colisionar(field, value, message):
    with pytest.raises(ValidationError, match=message):
        staging_settings(**{field: value})


def test_staging_rechaza_credenciales_whatsapp_meta():
    with pytest.raises(ValidationError, match="sin habilitación explícita"):
        staging_settings(whatsapp_access_token=SecretStr("synthetic-only"))


def test_staging_whatsapp_meta_exige_numero_y_cuenta_de_prueba_allowlisted():
    valores = {
        "staging_whatsapp_meta_enabled": True,
        "staging_whatsapp_meta_test_number_confirmed": True,
        "whatsapp_enabled": True,
        "whatsapp_provider": "meta",
        "public_api_url": "https://api.staging.turnelia.com.ar",
        "whatsapp_phone_number_id": "test-phone-123",
        "whatsapp_business_account_id": "test-business-456",
        "whatsapp_access_token": SecretStr("staging-test-access-token"),
        "whatsapp_verify_token": SecretStr("staging-test-verify-token"),
        "whatsapp_app_secret": SecretStr("staging-test-app-secret"),
        "whatsapp_api_version": "v99.0",
        "staging_whatsapp_phone_number_id_allowlist": "test-phone-123",
        "staging_whatsapp_business_account_id_allowlist": "test-business-456",
    }
    config = staging_settings(**valores)
    assert config.staging_whatsapp_meta_enabled

    with pytest.raises(ValidationError, match="número y una app de prueba"):
        staging_settings(**{**valores, "staging_whatsapp_meta_test_number_confirmed": False})
    with pytest.raises(ValidationError, match="allowlist de staging"):
        staging_settings(**{**valores, "whatsapp_phone_number_id": "production-phone"})
    with pytest.raises(ValidationError, match="subdominio staging dedicado"):
        staging_settings(**{**valores, "public_api_url": "https://api.turnelia.com.ar"})


def test_resend_staging_exige_allowlist_y_solo_envia_a_destinatarios_permitidos(monkeypatch):
    with pytest.raises(ValidationError, match="STAGING_EMAIL_ALLOWLIST"):
        staging_settings(
            staging_email_send_enabled=True,
            email_provider="resend",
            resend_api_key=SecretStr("synthetic-api-key"),
            email_from="Turnelia Staging <no-reply@example.invalid>",
        )

    config = staging_settings(
        staging_email_send_enabled=True,
        staging_email_allowlist="prueba@example.com, otra@example.net",
        email_provider="resend",
        resend_api_key=SecretStr("synthetic-api-key"),
        email_from="Turnelia Staging <no-reply@example.invalid>",
    )
    from app.services import email_service

    provider = email_service.obtener_email_provider(config)
    assert isinstance(provider, ResendEmailProvider)

    def no_network(*args, **kwargs):
        raise AssertionError("El provider no debe contactar Resend para destinatario no permitido.")

    monkeypatch.setattr(email_service.requests, "post", no_network)
    with pytest.raises(EmailDeliveryError, match="no está autorizado"):
        provider.enviar(TransactionalEmail("externo@example.org", "test", "body", "body"))


def test_email_staging_permanece_en_memoria_por_defecto():
    from app.services.email_service import InMemoryEmailProvider, obtener_email_provider

    config = staging_settings()
    assert isinstance(obtener_email_provider(config), InMemoryEmailProvider)


def test_generador_crea_secretos_fuera_del_repo_y_no_sobrescribe():
    with TemporaryDirectory() as temporary:
        target = Path(temporary) / "turnelia-staging.env"
        create_env_file(target)
        contents = target.read_text(encoding="utf-8")
        assert "STAGING_POSTGRES_DB=turnelia_staging" in contents
        assert "STAGING_EMAIL_SEND_ENABLED=false" in contents
        assert "WHATSAPP_ENABLED=false" in contents
        with pytest.raises(FileExistsError):
            create_env_file(target)


def test_generador_rechaza_secretos_dentro_del_repo():
    with pytest.raises(ValueError, match="fuera del repositorio"):
        create_env_file(Path(seed_staging.__file__).resolve().parents[2] / ".env.staging")


def test_semilla_requiere_modo_y_base_staging(monkeypatch):
    monkeypatch.setattr(seed_staging.settings, "app_env", "staging")
    valid = {
        "APP_ENV": "staging",
        "STAGING_SEED_ENABLED": "true",
        "DATABASE_URL": "postgresql+psycopg://fake:fake@db:5432/turnelia_staging",
        "STAGING_DEMO_PASSWORD": "synthetic-only",
    }
    seed_staging.validar_entorno(valid)

    for key, value in (
        ("APP_ENV", "production"),
        ("STAGING_SEED_ENABLED", "false"),
        ("DATABASE_URL", "postgresql+psycopg://fake:fake@prod-db:5432/turnelia_staging"),
        ("DATABASE_URL", "postgresql+psycopg://fake:fake@db:5432/turnelia"),
    ):
        invalid = {**valid, key: value}
        with pytest.raises(SystemExit):
            seed_staging.validar_entorno(invalid)


def test_semilla_rechaza_identidades_fuera_de_example_invalid(monkeypatch):
    monkeypatch.setattr(seed_staging.settings, "app_env", "staging")
    invalid = {
        "APP_ENV": "staging",
        "STAGING_SEED_ENABLED": "true",
        "DATABASE_URL": "postgresql+psycopg://fake:fake@db:5432/turnelia_staging",
        "STAGING_DEMO_PASSWORD": "synthetic-only",
        "STAGING_ADMIN_EMAIL": "real.person@example.com",
    }
    with pytest.raises(SystemExit, match="example.invalid"):
        seed_staging.validar_entorno(invalid)
