import os
import sys

from sqlalchemy import text

from app.core.security import generar_hash_password
from app.database.connection import SessionLocal
from app.models.cuenta import Cuenta
from app.models.cuenta_usuario import CuentaUsuario
from app.models.usuario import Usuario


E2E_EMAIL = "admin.e2e@example.com"


def validar_entorno() -> None:
    database_url = os.environ.get("DATABASE_URL", "")
    if os.environ.get("APP_ENV") != "test":
        raise SystemExit("Fixture E2E abortado: APP_ENV no es test.")
    if "127.0.0.1:55432" not in database_url:
        raise SystemExit("Fixture E2E abortado: host/puerto E2E no coincide.")
    if "/turnelia_e2e" not in database_url:
        raise SystemExit("Fixture E2E abortado: database E2E no coincide.")
    if os.environ.get("E2E_DATABASE_NAME") != "turnelia_e2e":
        raise SystemExit("Fixture E2E abortado: falta la identificación E2E.")
    if not os.environ.get("E2E_ADMIN_PASSWORD", "").strip():
        raise SystemExit("Fixture E2E abortado: falta E2E_ADMIN_PASSWORD.")


def main() -> None:
    validar_entorno()
    password = os.environ["E2E_ADMIN_PASSWORD"]
    db = SessionLocal()
    try:
        admin = db.query(Usuario).filter(Usuario.email == E2E_EMAIL).one_or_none()
        if admin is None:
            admin = Usuario(
                nombre="Administrador E2E",
                email=E2E_EMAIL,
                password_hash=generar_hash_password(password),
                rol="administrador",
                activo=True,
            )
            db.add(admin)
            db.flush()

        cuenta = db.query(Cuenta).filter(Cuenta.nombre == "Cuenta E2E").one_or_none()
        if cuenta is None:
            cuenta = Cuenta(nombre="Cuenta E2E", tipo="individual")
            db.add(cuenta)
            db.flush()

        membership = db.query(CuentaUsuario).filter(
            CuentaUsuario.cuenta_id == cuenta.id,
            CuentaUsuario.usuario_id == admin.id,
        ).one_or_none()
        if membership is None:
            db.add(CuentaUsuario(
                cuenta_id=cuenta.id,
                usuario_id=admin.id,
                rol_cuenta="propietario",
            ))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
