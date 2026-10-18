"""Create an exclusive staging environment file outside the repository."""

import argparse
import os
import secrets
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def generar_texto() -> str:
    postgres_password = secrets.token_urlsafe(48)
    return "\n".join([
        "STAGING_POSTGRES_USER=turnelia_staging",
        f"STAGING_POSTGRES_PASSWORD={postgres_password}",
        "STAGING_POSTGRES_DB=turnelia_staging",
        "STAGING_API_PORT=18081",
        "STAGING_FRONTEND_PORT=18080",
        "STAGING_BROWSER_API_URL=http://127.0.0.1:18081",
        "APP_ENV=staging",
        f"DATABASE_URL=postgresql+psycopg://turnelia_staging:{postgres_password}@db:5432/turnelia_staging",
        "APP_TIMEZONE=America/Argentina/Buenos_Aires",
        "FRONTEND_URL=http://127.0.0.1:18080",
        "PUBLIC_API_URL=http://127.0.0.1:18081",
        'CORS_ALLOWED_ORIGINS=["http://127.0.0.1:18080"]',
        f"JWT_SECRET_KEY={secrets.token_urlsafe(48)}",
        "JWT_ALGORITHM=HS256",
        "JWT_EXPIRE_MINUTES=60",
        "PASSWORD_RESET_EXPIRE_MINUTES=60",
        f"APPOINTMENT_ACTION_SECRET={secrets.token_urlsafe(48)}",
        f"STUDY_ACCESS_SECRET={secrets.token_urlsafe(48)}",
        "STUDY_ACCESS_TOKEN_TTL_SECONDS=2592000",
        "EMAIL_PROVIDER=in_memory",
        "EMAIL_FROM=Turnelia Staging <no-reply@example.invalid>",
        "RESEND_API_KEY=",
        "STAGING_EMAIL_SEND_ENABLED=false",
        "STAGING_EMAIL_ALLOWLIST=",
        "MERCADOPAGO_ENV=sandbox",
        "MERCADOPAGO_ACCESS_TOKEN=",
        "MERCADOPAGO_PUBLIC_KEY=",
        "MERCADOPAGO_WEBHOOK_SECRET=",
        "WHATSAPP_ENABLED=false",
        "WHATSAPP_PROVIDER=fake",
        "STAGING_WHATSAPP_META_ENABLED=false",
        "STAGING_WHATSAPP_META_TEST_NUMBER_CONFIRMED=false",
        "STAGING_WHATSAPP_PROVIDER=fake",
        "STAGING_WHATSAPP_PHONE_NUMBER_ID_ALLOWLIST=",
        "STAGING_WHATSAPP_BUSINESS_ACCOUNT_ID_ALLOWLIST=",
        "STAGING_WHATSAPP_RECIPIENT_ALLOWLIST=",
        "WHATSAPP_PHONE_NUMBER_ID=",
        "WHATSAPP_BUSINESS_ACCOUNT_ID=",
        "WHATSAPP_ACCESS_TOKEN=",
        "WHATSAPP_VERIFY_TOKEN=",
        "WHATSAPP_APP_SECRET=",
        "WHATSAPP_API_VERSION=",
        "OBJECT_STORAGE_PROVIDER=fake",
        "DEMO_SEED_ENABLED=false",
        "STAGING_SEED_ENABLED=false",
        f"STAGING_DEMO_PASSWORD={secrets.token_urlsafe(48)}",
        "",
    ])


def create_env_file(path: Path) -> Path:
    target = path.expanduser().resolve()
    try:
        target.relative_to(ROOT)
    except ValueError:
        pass
    else:
        raise ValueError("El archivo de secretos debe quedar fuera del repositorio.")
    target.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(target, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as output:
            output.write(generar_texto())
    except Exception:
        target.unlink(missing_ok=True)
        raise
    if os.name != "nt":
        os.chmod(target, 0o600)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Destino privado, por ejemplo /srv/secrets/turnelia-staging.env")
    args = parser.parse_args()
    try:
        target = create_env_file(args.path)
    except FileExistsError:
        print("El archivo ya existe; no se sobrescribió.", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"No se pudo crear el archivo staging ({type(error).__name__}).", file=sys.stderr)
        return 1
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(f"Configuración privada creada en {target}; secretos no mostrados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
