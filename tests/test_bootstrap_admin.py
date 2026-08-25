import pytest
from sqlalchemy.exc import IntegrityError

from app.scripts import bootstrap_admin
from app.core.security import (
    generar_hash_password,
    verificar_password,
)
from app.models.usuario import Usuario
from app.scripts.bootstrap_admin import (
    AdministradorExistenteError,
    ConfiguracionBootstrapAdmin,
    CreacionAdministradorError,
    EmailBootstrapEnUsoError,
    crear_primer_administrador,
)
from tests.conftest import SessionTest


@pytest.fixture
def db():
    sesion = SessionTest()

    try:
        yield sesion
    finally:
        sesion.close()


def crear_configuracion() -> ConfiguracionBootstrapAdmin:
    return ConfiguracionBootstrapAdmin(
        _env_file=None,
        bootstrap_admin_email="admin@mediturnos.example",
        bootstrap_admin_password="clave-inicial-muy-segura",
        bootstrap_admin_name="Administración",
    )


def test_bootstrap_crea_primer_administrador(db):
    administrador = crear_primer_administrador(
        db,
        crear_configuracion(),
    )

    assert administrador.nombre == "Administración"
    assert administrador.email == "admin@mediturnos.example"
    assert administrador.rol == "administrador"
    assert administrador.activo is True
    assert verificar_password(
        "clave-inicial-muy-segura",
        administrador.password_hash,
    )
    assert db.query(Usuario).count() == 1


def test_bootstrap_bloquea_si_ya_existe_administrador(db):
    existente = Usuario(
        nombre="Admin existente",
        email="otro-admin@mediturnos.example",
        password_hash=generar_hash_password("clave-existente"),
        rol="administrador",
        activo=True,
    )
    db.add(existente)
    db.commit()
    hash_original = existente.password_hash

    with pytest.raises(
        AdministradorExistenteError,
        match="Ya existe un usuario administrador",
    ):
        crear_primer_administrador(
            db,
            crear_configuracion(),
        )

    assert db.query(Usuario).count() == 1
    db.refresh(existente)
    assert existente.password_hash == hash_original


def test_bootstrap_bloquea_email_perteneciente_a_otro_usuario(db):
    existente = Usuario(
        nombre="Paciente existente",
        email="admin@mediturnos.example",
        password_hash=generar_hash_password("clave-existente"),
        rol="paciente",
        activo=False,
    )
    db.add(existente)
    db.commit()
    hash_original = existente.password_hash

    with pytest.raises(
        EmailBootstrapEnUsoError,
        match="ya pertenece a otro usuario",
    ):
        crear_primer_administrador(
            db,
            crear_configuracion(),
        )

    db.refresh(existente)
    assert existente.rol == "paciente"
    assert existente.activo is False
    assert existente.password_hash == hash_original


def test_bootstrap_hace_rollback_ante_fallo(db, monkeypatch):
    def commit_fallido():
        raise RuntimeError("fallo simulado")

    monkeypatch.setattr(db, "commit", commit_fallido)

    with pytest.raises(RuntimeError, match="fallo simulado"):
        crear_primer_administrador(
            db,
            crear_configuracion(),
        )

    assert db.query(Usuario).count() == 0


def test_bootstrap_sanitiza_error_sql_y_hace_rollback(
    db,
    monkeypatch,
):
    password = "clave-inicial-muy-segura"
    hash_sensible = "hash-generado-que-no-debe-exponerse"
    rollback_original = db.rollback
    rollback_ejecutado = False

    def generar_hash_controlado(password_recibido):
        assert password_recibido == password
        return hash_sensible

    def flush_fallido():
        raise IntegrityError(
            "INSERT INTO usuarios (...)",
            {
                "password_hash": hash_sensible,
                "password": password,
            },
            RuntimeError("fallo simulado"),
        )

    def registrar_rollback():
        nonlocal rollback_ejecutado
        rollback_ejecutado = True
        rollback_original()

    monkeypatch.setattr(
        bootstrap_admin,
        "generar_hash_password",
        generar_hash_controlado,
    )
    monkeypatch.setattr(db, "flush", flush_fallido)
    monkeypatch.setattr(db, "rollback", registrar_rollback)

    with pytest.raises(CreacionAdministradorError) as error:
        crear_primer_administrador(
            db,
            crear_configuracion(),
        )

    mensaje = str(error.value)

    assert rollback_ejecutado is True
    assert db.query(Usuario).count() == 0
    assert password not in mensaje
    assert hash_sensible not in mensaje
    assert "password_hash" not in mensaje
    assert "error de persistencia" in mensaje
