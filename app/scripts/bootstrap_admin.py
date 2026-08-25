from pydantic import EmailStr, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import generar_hash_password
from app.database.connection import SessionLocal
from app.models.usuario import Usuario


class AdministradorExistenteError(RuntimeError):
    pass


class EmailBootstrapEnUsoError(RuntimeError):
    pass


class CreacionAdministradorError(RuntimeError):
    pass


class ConfiguracionBootstrapAdmin(BaseSettings):
    bootstrap_admin_email: EmailStr
    bootstrap_admin_password: SecretStr = Field(
        min_length=12,
    )
    bootstrap_admin_name: str = Field(
        default="Administrador",
        min_length=1,
        max_length=100,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        hide_input_in_errors=True,
    )


def crear_primer_administrador(
    db: Session,
    configuracion: ConfiguracionBootstrapAdmin,
) -> Usuario:
    try:
        administrador_existente = (
            db.query(Usuario)
            .filter(Usuario.rol == "administrador")
            .first()
        )

        if administrador_existente is not None:
            raise AdministradorExistenteError(
                "Ya existe un usuario administrador. El bootstrap "
                "no realizó cambios."
            )

        email = str(configuracion.bootstrap_admin_email)
        usuario_mismo_email = (
            db.query(Usuario)
            .filter(Usuario.email == email)
            .first()
        )

        if usuario_mismo_email is not None:
            raise EmailBootstrapEnUsoError(
                "El email configurado ya pertenece a otro usuario. "
                "El bootstrap no modificó su cuenta."
            )

        administrador = Usuario(
            nombre=configuracion.bootstrap_admin_name.strip(),
            email=email,
            password_hash=generar_hash_password(
                configuracion.bootstrap_admin_password.get_secret_value()
            ),
            rol="administrador",
            activo=True,
        )

        db.add(administrador)
        db.flush()
        db.commit()
    except SQLAlchemyError:
        try:
            db.rollback()
        except SQLAlchemyError:
            pass

        raise CreacionAdministradorError(
            "No se pudo crear el primer administrador por un "
            "error de persistencia. No se guardaron cambios."
        ) from None
    except Exception:
        db.rollback()
        raise

    return administrador


def main() -> None:
    configuracion = ConfiguracionBootstrapAdmin()
    db = SessionLocal()

    try:
        crear_primer_administrador(db, configuracion)
    finally:
        db.close()

    print("Primer administrador creado correctamente.")


if __name__ == "__main__":
    main()
