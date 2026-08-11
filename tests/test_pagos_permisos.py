from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.core.dependencies import obtener_usuario_actual
from app.main import app
from app.models.especialidad import Especialidad
from app.models.paciente import Paciente
from app.models.pago import Pago
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.turno import Turno
from app.models.usuario import Usuario
from tests.conftest import SessionTest


@pytest.fixture
def escenario_pago():
    db = SessionTest()

    propietario = Usuario(
        nombre="Paciente propietario",
        email="propietario@example.com",
        password_hash="hash",
        rol="paciente",
    )
    paciente_ajeno = Usuario(
        nombre="Paciente ajeno",
        email="ajeno@example.com",
        password_hash="hash",
        rol="paciente",
    )
    administrador = Usuario(
        nombre="Administrador",
        email="admin@example.com",
        password_hash="hash",
        rol="administrador",
    )
    recepcionista = Usuario(
        nombre="Recepcionista",
        email="recepcion@example.com",
        password_hash="hash",
        rol="recepcionista",
    )
    profesional_usuario = Usuario(
        nombre="Profesional usuario",
        email="profesional@example.com",
        password_hash="hash",
        rol="profesional",
    )
    db.add_all([
        propietario,
        paciente_ajeno,
        administrador,
        recepcionista,
        profesional_usuario,
    ])
    db.flush()

    paciente = Paciente(
        usuario_id=propietario.id,
        nombre="Paciente",
        apellido="Propietario",
        dni="30111222",
        telefono="3515551234",
    )
    especialidad = Especialidad(
        nombre="Clínica Médica",
        duracion_turno_minutos=30,
    )
    profesional = Profesional(
        nombre="Ana",
        apellido="Gómez",
        matricula="MP-PAGOS-001",
    )
    db.add_all([
        paciente,
        especialidad,
        profesional,
    ])
    db.flush()

    prestacion = Prestacion(
        nombre="Consulta",
        duracion_minutos=30,
        precio=Decimal("15000.00"),
        modalidad="presencial",
        profesional_id=profesional.id,
        especialidad_id=especialidad.id,
    )
    db.add(prestacion)
    db.flush()

    turno = Turno(
        paciente_id=paciente.id,
        prestacion_id=prestacion.id,
        fecha_hora=datetime.now() + timedelta(days=1),
    )
    db.add(turno)
    db.flush()

    pago = Pago(
        turno_id=turno.id,
        preference_id="pref-existente",
        estado="pendiente",
        monto=Decimal("15000.00"),
        init_point="https://example.com/pagar",
    )
    db.add(pago)
    db.commit()

    datos = {
        "turno_id": turno.id,
        "propietario": propietario,
        "paciente_ajeno": paciente_ajeno,
        "administrador": administrador,
        "recepcionista": recepcionista,
        "profesional": profesional_usuario,
    }

    yield datos

    app.dependency_overrides.pop(
        obtener_usuario_actual,
        None,
    )
    db.close()


def autenticar_como(usuario):
    app.dependency_overrides[
        obtener_usuario_actual
    ] = lambda: usuario


@pytest.mark.parametrize(
    "clave_usuario",
    [
        "propietario",
        "administrador",
        "recepcionista",
    ],
)
@pytest.mark.parametrize(
    "metodo,ruta_sufijo,estado_esperado",
    [
        ("get", "", 200),
        ("post", "/preferencia", 201),
    ],
)
def test_pago_permite_propietario_y_personal_autorizado(
    client,
    escenario_pago,
    clave_usuario,
    metodo,
    ruta_sufijo,
    estado_esperado,
):
    autenticar_como(
        escenario_pago[clave_usuario]
    )
    ruta = (
        f"/pagos/turnos/{escenario_pago['turno_id']}"
        f"{ruta_sufijo}"
    )

    respuesta = getattr(client, metodo)(ruta)

    assert respuesta.status_code == estado_esperado
    assert respuesta.json()["turno_id"] == escenario_pago["turno_id"]


@pytest.mark.parametrize(
    "metodo,ruta_sufijo",
    [
        ("get", ""),
        ("post", "/preferencia"),
    ],
)
def test_pago_rechaza_paciente_ajeno(
    client,
    escenario_pago,
    metodo,
    ruta_sufijo,
):
    autenticar_como(
        escenario_pago["paciente_ajeno"]
    )
    ruta = (
        f"/pagos/turnos/{escenario_pago['turno_id']}"
        f"{ruta_sufijo}"
    )

    respuesta = getattr(client, metodo)(ruta)

    assert respuesta.status_code == 403


@pytest.mark.parametrize(
    "metodo,ruta_sufijo",
    [
        ("get", ""),
        ("post", "/preferencia"),
    ],
)
def test_pago_rechaza_profesional(
    client,
    escenario_pago,
    metodo,
    ruta_sufijo,
):
    autenticar_como(
        escenario_pago["profesional"]
    )
    ruta = (
        f"/pagos/turnos/{escenario_pago['turno_id']}"
        f"{ruta_sufijo}"
    )

    respuesta = getattr(client, metodo)(ruta)

    assert respuesta.status_code == 403


@pytest.mark.parametrize(
    "metodo,ruta_sufijo",
    [
        ("get", ""),
        ("post", "/preferencia"),
    ],
)
def test_pago_exige_autenticacion(
    client,
    escenario_pago,
    metodo,
    ruta_sufijo,
):
    ruta = (
        f"/pagos/turnos/{escenario_pago['turno_id']}"
        f"{ruta_sufijo}"
    )

    respuesta = getattr(client, metodo)(ruta)

    assert respuesta.status_code in {401, 403}
