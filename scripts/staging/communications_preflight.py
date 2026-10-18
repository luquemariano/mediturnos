"""Preflight fail-closed para configuración de comunicaciones de staging.

No crea providers, abre conexiones ni envía mensajes. La salida sólo contiene
nombres de variables, estados y resultados de validación; nunca valores.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_RE = re.compile(r"^\+?[1-9]\d{7,14}$")
CALLBACK = "https://api.staging.turnelia.com.ar/webhooks/whatsapp"
DEFAULTS = {
    "APP_ENV": "",
    "EMAIL_PROVIDER": "in_memory",
    "STAGING_EMAIL_SEND_ENABLED": "false",
    "WHATSAPP_PROVIDER": "fake",
    "WHATSAPP_ENABLED": "false",
    "STAGING_WHATSAPP_META_ENABLED": "false",
    "STAGING_WHATSAPP_PROVIDER": "fake",
}


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[name] = value
    return values


def _bool(values: dict[str, str], key: str) -> bool:
    return values.get(key, DEFAULTS.get(key, "")).strip().lower() == "true"


def validate(values: dict[str, str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    checks: list[str] = []
    env = values.get("APP_ENV", "")
    checks.append(f"APP_ENV: {'OK' if env == 'staging' else 'FALTA/INVÁLIDO'}")
    if env != "staging":
        errors.append("APP_ENV debe ser exactamente staging.")

    email_provider = values.get("EMAIL_PROVIDER", DEFAULTS["EMAIL_PROVIDER"])
    email_enabled = _bool(values, "STAGING_EMAIL_SEND_ENABLED")
    checks.append(f"EMAIL_PROVIDER: {'OK' if email_provider in {'in_memory', 'resend'} else 'INVÁLIDO'}")
    if email_provider not in {"in_memory", "resend"}:
        errors.append("EMAIL_PROVIDER no está soportado.")
    if not email_enabled:
        if email_provider != "in_memory":
            errors.append("Email real deshabilitado requiere EMAIL_PROVIDER=in_memory.")
        checks.append("Email real: deshabilitado")
    else:
        required = ("RESEND_API_KEY", "EMAIL_FROM", "STAGING_EMAIL_ALLOWLIST")
        missing = [name for name in required if not values.get(name, "").strip()]
        for name in required:
            checks.append(f"{name}: {'presente' if values.get(name, '').strip() else 'FALTA'}")
        addresses = [item.strip().lower() for item in values.get("STAGING_EMAIL_ALLOWLIST", "").split(",") if item.strip()]
        if email_provider != "resend":
            errors.append("Email real requiere EMAIL_PROVIDER=resend.")
        if missing:
            errors.append("Email real requiere las variables indicadas como faltantes.")
        if not addresses or any(not EMAIL_RE.fullmatch(item) for item in addresses):
            errors.append("STAGING_EMAIL_ALLOWLIST debe contener correos válidos.")
        if len(set(addresses)) != len(addresses):
            errors.append("STAGING_EMAIL_ALLOWLIST no debe repetir destinatarios.")
        checks.append(f"STAGING_EMAIL_ALLOWLIST: {'válida' if addresses and all(EMAIL_RE.fullmatch(item) for item in addresses) else 'FALTA/INVÁLIDA'}")

    wa_meta_enabled = _bool(values, "STAGING_WHATSAPP_META_ENABLED")
    # Compose transforma estas dos variables staging en las variables runtime.
    wa_enabled = wa_meta_enabled if "STAGING_WHATSAPP_META_ENABLED" in values else _bool(values, "WHATSAPP_ENABLED")
    wa_provider = values.get("STAGING_WHATSAPP_PROVIDER", values.get("WHATSAPP_PROVIDER", DEFAULTS["WHATSAPP_PROVIDER"]))
    checks.append(f"WHATSAPP_PROVIDER: {'OK' if wa_provider in {'fake', 'meta'} else 'INVÁLIDO'}")
    if wa_provider not in {"fake", "meta"}:
        errors.append("WHATSAPP_PROVIDER no está soportado.")
    if not wa_enabled and not wa_meta_enabled:
        if wa_provider != "fake":
            errors.append("WhatsApp real deshabilitado requiere WHATSAPP_PROVIDER=fake.")
        checks.append("WhatsApp real: deshabilitado")
    else:
        ids = (
            ("WHATSAPP_PHONE_NUMBER_ID", "STAGING_WHATSAPP_PHONE_NUMBER_ID_ALLOWLIST"),
            ("WHATSAPP_BUSINESS_ACCOUNT_ID", "STAGING_WHATSAPP_BUSINESS_ACCOUNT_ID_ALLOWLIST"),
        )
        required = (
            "WHATSAPP_ACCESS_TOKEN", "WHATSAPP_VERIFY_TOKEN", "WHATSAPP_APP_SECRET",
            "WHATSAPP_API_VERSION", "STAGING_WHATSAPP_RECIPIENT_ALLOWLIST",
        )
        if wa_provider != "meta" or not wa_enabled or not wa_meta_enabled:
            errors.append("WhatsApp real requiere WHATSAPP_ENABLED, proveedor meta y bandera staging explícita.")
        if not _bool(values, "STAGING_WHATSAPP_META_TEST_NUMBER_CONFIRMED"):
            errors.append("Debe confirmarse que la app y el número Meta son de prueba.")
        for name in required:
            present = bool(values.get(name, "").strip())
            checks.append(f"{name}: {'presente' if present else 'FALTA'}")
            if not present:
                errors.append(f"Falta {name}.")
        recipients = [item.strip() for item in values.get("STAGING_WHATSAPP_RECIPIENT_ALLOWLIST", "").split(",") if item.strip()]
        if not recipients or any(not PHONE_RE.fullmatch(item) for item in recipients):
            errors.append("STAGING_WHATSAPP_RECIPIENT_ALLOWLIST debe incluir teléfonos de prueba en formato internacional.")
        checks.append(f"STAGING_WHATSAPP_RECIPIENT_ALLOWLIST: {'válida' if recipients and all(PHONE_RE.fullmatch(item) for item in recipients) else 'FALTA/INVÁLIDA'}")
        for value_name, allowlist_name in ids:
            value = values.get(value_name, "").strip()
            allowlist = {item.strip() for item in values.get(allowlist_name, "").split(",") if item.strip()}
            checks.append(f"{value_name} / allowlist: {'coincide' if value and value in allowlist else 'FALTA/NO COINCIDE'}")
            if not value or value not in allowlist:
                errors.append(f"{value_name} debe coincidir con {allowlist_name}.")
        public_url = values.get("PUBLIC_API_URL", "").strip()
        parsed = urlparse(public_url)
        callback_ok = parsed.scheme == "https" and parsed.netloc == "api.staging.turnelia.com.ar" and parsed.path in {"", "/"}
        checks.append(f"PUBLIC_API_URL/webhook HTTPS: {'OK' if callback_ok else 'FALTA/INVÁLIDA'}")
        if not callback_ok:
            errors.append("PUBLIC_API_URL debe ser https://api.staging.turnelia.com.ar para el webhook Meta.")
        try:
            from app.integrations.messaging import DEFAULT_TEMPLATE_MAPPING
            template = DEFAULT_TEMPLATE_MAPPING.get("appointment_reminder_v2")
            template_ok = bool(template and template.name == "appointment_reminder_v2" and template.language_code == "es_AR" and template.button_parameter_keys == ("confirm_token", "cancel_token"))
        except Exception:
            template_ok = False
        checks.append(f"Plantilla WhatsApp de recordatorio: {'configurada en código' if template_ok else 'FALTA/INVÁLIDA'}")
        if not template_ok:
            errors.append("Falta configuración de plantilla de recordatorio confirm/cancel.")

    return checks, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", required=True, type=Path, help="Archivo privado de entorno staging")
    args = parser.parse_args(argv)
    try:
        values = _parse_env_file(args.env_file)
    except OSError:
        print("Preflight rechazado: no se pudo leer el archivo de entorno.", file=sys.stderr)
        return 2
    checks, errors = validate(values)
    for check in checks:
        print(f"[{ 'OK' if not any(check.split(': ', 1)[1].startswith(x) for x in ('FALTA', 'INVÁLIDO', 'NO COINCIDE')) else 'REVISAR'}] {check}")
    if errors:
        print(f"Preflight rechazado: {len(errors)} condición(es) requieren corrección.", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Preflight aprobado. No se crearon providers ni se enviaron mensajes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
