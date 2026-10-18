from scripts.staging.communications_preflight import CALLBACK, validate


def staging_defaults():
    return {
        "APP_ENV": "staging",
        "EMAIL_PROVIDER": "in_memory",
        "STAGING_EMAIL_SEND_ENABLED": "false",
        "WHATSAPP_PROVIDER": "fake",
        "WHATSAPP_ENABLED": "false",
        "STAGING_WHATSAPP_META_ENABLED": "false",
        "STAGING_WHATSAPP_PROVIDER": "fake",
    }


def test_preflight_accepts_safe_staging_defaults_without_provider_credentials():
    checks, errors = validate(staging_defaults())
    assert not errors
    assert "Email real: deshabilitado" in checks
    assert "WhatsApp real: deshabilitado" in checks


def test_preflight_rejects_non_staging_and_production_provider_configuration():
    values = staging_defaults() | {"APP_ENV": "production", "EMAIL_PROVIDER": "resend"}
    _, errors = validate(values)
    assert any("exactamente staging" in error for error in errors)
    assert any("Email real deshabilitado" in error for error in errors)


def test_preflight_validates_real_email_configuration_without_echoing_values():
    values = staging_defaults() | {
        "STAGING_EMAIL_SEND_ENABLED": "true",
        "EMAIL_PROVIDER": "resend",
        "RESEND_API_KEY": "secret-never-print",
        "EMAIL_FROM": "Turnelia <qa@example.test>",
        "STAGING_EMAIL_ALLOWLIST": "qa@example.test,also@example.test",
    }
    checks, errors = validate(values)
    assert not errors
    assert "RESEND_API_KEY: presente" in checks
    assert "STAGING_EMAIL_ALLOWLIST: válida" in checks
    assert "secret-never-print" not in str(checks + errors)
    assert "qa@example.test" not in str(checks + errors)


def test_preflight_rejects_invalid_real_email_allowlist():
    values = staging_defaults() | {
        "STAGING_EMAIL_SEND_ENABLED": "true", "EMAIL_PROVIDER": "resend",
        "RESEND_API_KEY": "x", "EMAIL_FROM": "sender",
        "STAGING_EMAIL_ALLOWLIST": "not-an-address",
    }
    _, errors = validate(values)
    assert any("STAGING_EMAIL_ALLOWLIST" in error for error in errors)


def test_preflight_validates_whatsapp_allowlists_webhook_and_builtin_template():
    values = staging_defaults() | {
        "WHATSAPP_ENABLED": "false", "WHATSAPP_PROVIDER": "fake",
        "STAGING_WHATSAPP_PROVIDER": "meta",
        "STAGING_WHATSAPP_META_ENABLED": "true",
        "STAGING_WHATSAPP_META_TEST_NUMBER_CONFIRMED": "true",
        "WHATSAPP_PHONE_NUMBER_ID": "test-phone-id",
        "STAGING_WHATSAPP_PHONE_NUMBER_ID_ALLOWLIST": "test-phone-id",
        "WHATSAPP_BUSINESS_ACCOUNT_ID": "test-business-id",
        "STAGING_WHATSAPP_BUSINESS_ACCOUNT_ID_ALLOWLIST": "test-business-id",
        "WHATSAPP_ACCESS_TOKEN": "secret-access", "WHATSAPP_VERIFY_TOKEN": "secret-verify",
        "WHATSAPP_APP_SECRET": "secret-app", "WHATSAPP_API_VERSION": "v99.0",
        "STAGING_WHATSAPP_RECIPIENT_ALLOWLIST": "+5493511234567",
        "PUBLIC_API_URL": CALLBACK.removesuffix("/webhooks/whatsapp"),
    }
    checks, errors = validate(values)
    assert not errors
    assert "Plantilla WhatsApp de recordatorio: configurada en código" in checks
    assert "secret-access" not in str(checks + errors)
    assert "+5493511234567" not in str(checks + errors)


def test_preflight_rejects_whatsapp_recipient_outside_explicit_allowlist_configuration():
    values = staging_defaults() | {
        "WHATSAPP_ENABLED": "false", "WHATSAPP_PROVIDER": "fake",
        "STAGING_WHATSAPP_PROVIDER": "meta",
        "STAGING_WHATSAPP_META_ENABLED": "true",
        "STAGING_WHATSAPP_META_TEST_NUMBER_CONFIRMED": "true",
        "WHATSAPP_PHONE_NUMBER_ID": "phone", "STAGING_WHATSAPP_PHONE_NUMBER_ID_ALLOWLIST": "phone",
        "WHATSAPP_BUSINESS_ACCOUNT_ID": "business", "STAGING_WHATSAPP_BUSINESS_ACCOUNT_ID_ALLOWLIST": "business",
        "WHATSAPP_ACCESS_TOKEN": "secret", "WHATSAPP_VERIFY_TOKEN": "secret",
        "WHATSAPP_APP_SECRET": "secret", "WHATSAPP_API_VERSION": "v99.0",
        "STAGING_WHATSAPP_RECIPIENT_ALLOWLIST": "",
        "PUBLIC_API_URL": "http://127.0.0.1:18081",
    }
    _, errors = validate(values)
    assert any("STAGING_WHATSAPP_RECIPIENT_ALLOWLIST" in error for error in errors)
    assert any("PUBLIC_API_URL" in error for error in errors)
