from decimal import Decimal

import pytest
from pydantic import SecretStr

from app.core.config import settings
from app.core.security import (
    generar_hash_password,
    verificar_password,
)
from app.models.especialidad import Especialidad
from app.models.paciente import Paciente
from app.models.pago import Pago
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.turno import Turno
from app.models.usuario import Usuario
from app.scripts.seed import (
    CuentaAdminNoDemoError,
    ConfiguracionSeedInvalidaError,
    MARCA_TURNO_DEMO,
    TurnosDemoConPagosError,
    cargar_datos_demo,
)
from tests.conftest import SessionTest


EMAIL_DEMO = "admin.seed@mediturnos.demo"
PASSWORD_DEMO = "PasswordDemoSegura123!"


@pytest.fixture
def db():
    sesion = SessionTest()

    try:
        yield sesion
    finally:
        sesion.close()


@pytest.fixture(autouse=True)
def configurar_seed(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "test")
    monkeypatch.setattr(settings, "demo_seed_enabled", True)
    monkeypatch.setattr(settings, "demo_admin_email", EMAIL_DEMO)
    monkeypatch.setattr(
        settings,
        "demo_admin_password",
        SecretStr(PASSWORD_DEMO),
    )
    monkeypatch.setattr(
        settings,
        "demo_admin_reset_password",
        False,
    )


def test_seed_se_bloquea_siempre_en_production(
    db,
    monkeypatch,
):
    monkeypatch.setattr(settings, "app_env", "production")

    with pytest.raises(
        ConfiguracionSeedInvalidaError,
        match="no puede ejecutarse en production",
    ):
        cargar_datos_demo(db)

    assert db.query(Usuario).count() == 0


def test_seed_se_bloquea_si_no_esta_habilitado(
    db,
    monkeypatch,
):
    monkeypatch.setattr(settings, "demo_seed_enabled", False)

    with pytest.raises(
        ConfiguracionSeedInvalidaError,
        match="DEMO_SEED_ENABLED=true",
    ):
        cargar_datos_demo(db)

    assert db.query(Usuario).count() == 0


@pytest.mark.parametrize(
    ("email", "password", "mensaje"),
    [
        (None, PASSWORD_DEMO, "DEMO_ADMIN_EMAIL"),
        (EMAIL_DEMO, None, "DEMO_ADMIN_PASSWORD"),
    ],
)
def test_seed_rechaza_credenciales_faltantes(
    db,
    monkeypatch,
    email,
    password,
    mensaje,
):
    monkeypatch.setattr(settings, "demo_admin_email", email)
    monkeypatch.setattr(
        settings,
        "demo_admin_password",
        SecretStr(password) if password else None,
    )

    with pytest.raises(
        ConfiguracionSeedInvalidaError,
        match=mensaje,
    ):
        cargar_datos_demo(db)

    assert db.query(Usuario).count() == 0


def test_seed_crea_administrador_demo(db):
    cargar_datos_demo(db)

    administrador = (
        db.query(Usuario)
        .filter(Usuario.email == EMAIL_DEMO)
        .one()
    )

    assert administrador.nombre == "Administrador Demo"
    assert administrador.rol == "administrador"
    assert administrador.activo is True
    assert verificar_password(
        PASSWORD_DEMO,
        administrador.password_hash,
    )


def test_seed_no_cambia_password_existente_sin_reset(
    db,
):
    password_original = "PasswordOriginal123!"
    administrador = Usuario(
        nombre="Administrador Demo",
        email=EMAIL_DEMO,
        password_hash=generar_hash_password(password_original),
        rol="administrador",
        activo=True,
    )
    db.add(administrador)
    db.commit()

    cargar_datos_demo(db)
    db.refresh(administrador)

    assert verificar_password(
        password_original,
        administrador.password_hash,
    )
    assert not verificar_password(
        PASSWORD_DEMO,
        administrador.password_hash,
    )


def test_seed_resetea_password_solo_de_forma_explicita(
    db,
    monkeypatch,
):
    administrador = Usuario(
        nombre="Administrador Demo",
        email=EMAIL_DEMO,
        password_hash=generar_hash_password("PasswordOriginal123!"),
        rol="administrador",
        activo=True,
    )
    db.add(administrador)
    db.commit()
    monkeypatch.setattr(
        settings,
        "demo_admin_reset_password",
        True,
    )

    cargar_datos_demo(db)
    db.refresh(administrador)

    assert verificar_password(
        PASSWORD_DEMO,
        administrador.password_hash,
    )


def test_seed_no_escala_una_cuenta_que_no_es_demo(db):
    usuario = Usuario(
        nombre="Usuario Real",
        email=EMAIL_DEMO,
        password_hash=generar_hash_password("PasswordOriginal123!"),
        rol="paciente",
        activo=False,
    )
    db.add(usuario)
    db.commit()

    with pytest.raises(
        CuentaAdminNoDemoError,
        match="no puede identificarse inequívocamente",
    ):
        cargar_datos_demo(db)

    db.refresh(usuario)
    assert usuario.nombre == "Usuario Real"
    assert usuario.rol == "paciente"
    assert usuario.activo is False


def test_seed_bloquea_turnos_demo_con_pagos_y_hace_rollback(
    db,
):
    cargar_datos_demo(db)
    descripcion_divergente = (
        "Descripción modificada antes del seed fallido."
    )
    especialidad = (
        db.query(Especialidad)
        .filter(Especialidad.nombre == "Clínica Médica")
        .one()
    )
    especialidad.descripcion = descripcion_divergente

    turno = (
        db.query(Turno)
        .filter(
            Turno.observaciones.like(
                f"{MARCA_TURNO_DEMO}%",
            )
        )
        .first()
    )
    assert turno is not None

    pago = Pago(
        turno_id=turno.id,
        estado="pendiente",
        monto=Decimal("18000.00"),
    )
    db.add(pago)
    db.commit()
    id_turno = turno.id
    id_pago = pago.id
    id_especialidad = especialidad.id
    ids_turnos_antes = {
        item.id
        for item in db.query(Turno).all()
    }

    with pytest.raises(
        TurnosDemoConPagosError,
        match="tienen pagos asociados",
    ):
        cargar_datos_demo(db)

    assert {
        item.id
        for item in db.query(Turno).all()
    } == ids_turnos_antes
    assert db.query(Turno).filter(Turno.id == id_turno).one()
    assert db.query(Pago).filter(Pago.id == id_pago).one()
    especialidad_persistida = (
        db.query(Especialidad)
        .filter(Especialidad.id == id_especialidad)
        .one()
    )
    assert (
        especialidad_persistida.descripcion
        == descripcion_divergente
    )


def test_seed_es_idempotente_en_registros_principales(db):
    cargar_datos_demo(db)
    cargar_datos_demo(db)

    assert db.query(Usuario).count() == 1
    assert db.query(Especialidad).count() == 4
    assert db.query(Profesional).count() == 5
    assert db.query(Prestacion).count() == 7
    assert db.query(Paciente).count() == 8
    assert db.query(Turno).count() == 15
