from decimal import Decimal
from datetime import time

import pytest
from pydantic import SecretStr

from app.core.config import settings
from app.core.security import (
    generar_hash_password,
    verificar_password,
)
from app.models.especialidad import Especialidad
from app.models.disponibilidad import Disponibilidad
from app.models.paciente import Paciente
from app.models.pago import Pago
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.profesional_paciente import ProfesionalPaciente
from app.models.turno import Turno
from app.models.usuario import Usuario
from app.models.cuenta import Cuenta
from app.models.cuenta_usuario import CuentaUsuario
from app.models.suscripcion import Suscripcion
from app.scripts.seed import (
    CuentaAdminNoDemoError,
    CuentaProfesionalNoDemoError,
    ConfiguracionSeedInvalidaError,
    EMAIL_ADMIN_DEMO_LEGACY,
    EMAIL_PROFESIONAL_DEMO_LEGACY,
    MARCA_TURNO_DEMO,
    TurnosDemoConPagosError,
    cargar_datos_demo,
    construir_fecha,
)
from app.core.datetime_utils import fecha_actual_negocio
from tests.conftest import SessionTest


EMAIL_DEMO = "admin.seed@mediturnos.com.ar"
PASSWORD_DEMO = "PasswordDemoSegura123!"
EMAIL_PROFESIONAL_DEMO = "profesional.seed@mediturnos.com.ar"
PASSWORD_PROFESIONAL_DEMO = "PasswordProfesionalSegura123!"


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
    monkeypatch.setattr(
        settings,
        "demo_professional_email",
        EMAIL_PROFESIONAL_DEMO,
    )
    monkeypatch.setattr(
        settings,
        "demo_professional_password",
        SecretStr(PASSWORD_PROFESIONAL_DEMO),
    )
    monkeypatch.setattr(
        settings,
        "demo_professional_reset_password",
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
    "atributo",
    ["demo_admin_email", "demo_professional_email"],
)
def test_seed_rechaza_email_demo_local_invalido(db, monkeypatch, atributo):
    monkeypatch.setattr(
        settings,
        atributo,
        "usuario.demo@mediturnos.local",
    )

    with pytest.raises(
        ConfiguracionSeedInvalidaError,
        match="debe ser un email válido",
    ):
        cargar_datos_demo(db)

    assert db.query(Usuario).count() == 0


def test_seed_acepta_emails_demo_validos(db):
    cargar_datos_demo(db)

    assert (
        db.query(Usuario)
        .filter(Usuario.email == EMAIL_DEMO)
        .one()
    )
    assert (
        db.query(Usuario)
        .filter(Usuario.email == EMAIL_PROFESIONAL_DEMO)
        .one()
    )


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


def test_seed_crea_y_vincula_usuario_profesional_demo(db):
    cargar_datos_demo(db)

    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == EMAIL_PROFESIONAL_DEMO)
        .one()
    )
    profesional = (
        db.query(Profesional)
        .filter(Profesional.matricula == "MP-DEMO-PSIQ-001")
        .one()
    )

    assert usuario.nombre == "Profesional Demo"
    assert usuario.rol == "profesional"
    assert usuario.activo is True
    assert profesional.usuario_id == usuario.id
    assert usuario.profesional is profesional
    assert verificar_password(
        PASSWORD_PROFESIONAL_DEMO,
        usuario.password_hash,
    )


def test_seed_no_cambia_password_profesional_sin_reset(db):
    cargar_datos_demo(db)
    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == EMAIL_PROFESIONAL_DEMO)
        .one()
    )
    password_hash_original = generar_hash_password(
        "PasswordProfesionalOriginal123!"
    )
    usuario.password_hash = password_hash_original
    db.commit()

    cargar_datos_demo(db)
    db.refresh(usuario)

    assert usuario.password_hash == password_hash_original


def test_seed_rechaza_email_profesional_ocupado_y_hace_rollback(db):
    usuario_real = Usuario(
        nombre="Usuario Real",
        email=EMAIL_PROFESIONAL_DEMO,
        password_hash=generar_hash_password("PasswordOriginal123!"),
        rol="paciente",
        activo=True,
    )
    db.add(usuario_real)
    db.commit()

    with pytest.raises(
        CuentaProfesionalNoDemoError,
        match="no puede identificarse inequívocamente",
    ):
        cargar_datos_demo(db)

    db.refresh(usuario_real)
    assert usuario_real.nombre == "Usuario Real"
    assert usuario_real.rol == "paciente"
    assert db.query(Profesional).count() == 0


def test_seed_migra_email_legacy_profesional_y_preserva_vinculo(
    db,
    monkeypatch,
):
    monkeypatch.setattr(settings, "app_env", "demo")
    cargar_datos_demo(db)
    usuario = (
        db.query(Usuario)
        .filter(Usuario.email == EMAIL_PROFESIONAL_DEMO)
        .one()
    )
    profesional_id = usuario.profesional.id
    usuario_id = usuario.id
    usuario.email = EMAIL_PROFESIONAL_DEMO_LEGACY
    db.commit()

    cargar_datos_demo(db)
    cargar_datos_demo(db)

    migrado = db.query(Usuario).filter(Usuario.id == usuario_id).one()
    assert migrado.email == EMAIL_PROFESIONAL_DEMO
    assert migrado.profesional.id == profesional_id
    assert migrado.profesional.usuario_id == usuario_id
    assert db.query(Usuario).filter(
        Usuario.rol == "profesional"
    ).count() == 1


def test_seed_migra_email_legacy_administrador(db, monkeypatch):
    monkeypatch.setattr(settings, "app_env", "demo")
    cargar_datos_demo(db)
    administrador = (
        db.query(Usuario).filter(Usuario.email == EMAIL_DEMO).one()
    )
    administrador_id = administrador.id
    administrador.email = EMAIL_ADMIN_DEMO_LEGACY
    db.commit()

    cargar_datos_demo(db)

    migrado = db.query(Usuario).filter(Usuario.id == administrador_id).one()
    assert migrado.email == EMAIL_DEMO


def test_seed_no_modifica_usuario_legacy_profesional_incompatible(db):
    usuario_real = Usuario(
        nombre="Usuario Real",
        email=EMAIL_PROFESIONAL_DEMO_LEGACY,
        password_hash=generar_hash_password("PasswordOriginal123!"),
        rol="paciente",
        activo=True,
    )
    db.add(usuario_real)
    db.commit()

    cargar_datos_demo(db)

    db.refresh(usuario_real)
    assert usuario_real.email == EMAIL_PROFESIONAL_DEMO_LEGACY
    assert usuario_real.nombre == "Usuario Real"
    assert usuario_real.rol == "paciente"


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

    assert db.query(Usuario).count() == 2
    assert db.query(Especialidad).count() == 36
    assert db.query(Profesional).count() == 5
    assert db.query(Prestacion).count() == 7
    assert db.query(Paciente).count() == 8
    assert db.query(Turno).count() == 21
    assert db.query(Disponibilidad).count() == 2
    assert db.query(ProfesionalPaciente).count() == 8
    assert db.query(Cuenta).count() == 5
    assert db.query(Suscripcion).count() == 5
    assert db.query(CuentaUsuario).count() == 1
    assert all(item.status == "active" for item in db.query(Suscripcion).all())


def test_seed_vincula_y_reactiva_pacientes_demo_con_sofia(db):
    cargar_datos_demo(db)
    profesional = (
        db.query(Profesional)
        .filter(Profesional.matricula == "MP-DEMO-PSIQ-001")
        .one()
    )
    relaciones = (
        db.query(ProfesionalPaciente)
        .filter(ProfesionalPaciente.profesional_id == profesional.id)
        .all()
    )

    assert len(relaciones) == 8
    assert all(relacion.activo for relacion in relaciones)

    relaciones[0].activo = False
    db.commit()

    cargar_datos_demo(db)

    relaciones_actualizadas = (
        db.query(ProfesionalPaciente)
        .filter(ProfesionalPaciente.profesional_id == profesional.id)
        .all()
    )
    assert len(relaciones_actualizadas) == 8
    assert all(relacion.activo for relacion in relaciones_actualizadas)


def test_seed_crea_jornada_representativa_para_sofia(db):
    cargar_datos_demo(db)
    profesional = (
        db.query(Profesional)
        .filter(Profesional.matricula == "MP-DEMO-PSIQ-001")
        .one()
    )
    inicio = construir_fecha(0, 0, 0)
    fin = construir_fecha(1, 0, 0)
    turnos = (
        db.query(Turno)
        .filter(
            Turno.profesional_id == profesional.id,
            Turno.fecha_hora >= inicio,
            Turno.fecha_hora < fin,
        )
        .order_by(Turno.fecha_hora)
        .all()
    )

    assert [turno.estado for turno in turnos] == [
        "finalizado",
        "confirmado",
        "ausente",
        "confirmado",
        "reservado",
        "cancelado",
    ]
    assert all(
        anterior.fecha_fin <= siguiente.fecha_hora
        for anterior, siguiente in zip(turnos, turnos[1:])
    )
    disponibilidades = (
        db.query(Disponibilidad)
        .filter(
            Disponibilidad.profesional_id == profesional.id,
            Disponibilidad.dia_semana
            == fecha_actual_negocio().weekday(),
            Disponibilidad.activa.is_(True),
        )
        .order_by(Disponibilidad.hora_inicio)
        .all()
    )
    assert [
        (item.hora_inicio, item.hora_fin)
        for item in disponibilidades
    ] == [(time(8), time(12)), (time(14), time(19))]
