from datetime import datetime, time, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.disponibilidad import Disponibilidad
from app.models.especialidad import Especialidad
from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.turno import Turno
from app.core.datetime_utils import (
    desde_base_utc,
    fecha_hora_civil_a_utc,
    utc_a_zona_negocio,
)
from app.schemas.turno import TurnoCrear, TurnoReprogramar
from app.services.turno_service import crear_turno, reprogramar_turno
from tests.conftest import SessionTest


@pytest.fixture
def escenario_turnos():
    db = SessionTest()
    fecha = (datetime.now() + timedelta(days=7)).date()

    paciente = Paciente(
        nombre="Ana",
        apellido="Paciente",
        dni="30111222",
        telefono="3515551234",
    )
    profesional = Profesional(
        nombre="Carlos",
        apellido="Profesional",
        matricula="MP-SOLAP-001",
    )
    especialidad = Especialidad(
        nombre="Clínica Médica",
        duracion_turno_minutos=30,
    )
    db.add_all([paciente, profesional, especialidad])
    db.flush()

    prestaciones = {}

    for duracion in (30, 60):
        prestacion = Prestacion(
            nombre=f"Consulta {duracion}",
            duracion_minutos=duracion,
            precio=Decimal("15000.00"),
            modalidad="presencial",
            profesional_id=profesional.id,
            especialidad_id=especialidad.id,
        )
        db.add(prestacion)
        db.flush()
        prestaciones[duracion] = prestacion

    db.add(
        Disponibilidad(
            profesional_id=profesional.id,
            dia_semana=fecha.weekday(),
            hora_inicio=time(8, 0),
            hora_fin=time(18, 0),
        )
    )
    db.commit()

    yield {
        "db": db,
        "fecha": fecha,
        "paciente": paciente,
        "prestaciones": prestaciones,
    }

    db.close()


def crear_existente(
    escenario,
    hora_inicio,
    duracion=60,
    estado="reservado",
):
    turno = Turno(
        paciente_id=escenario["paciente"].id,
        prestacion_id=escenario["prestaciones"][duracion].id,
        fecha_hora=fecha_hora_civil_a_utc(
            escenario["fecha"],
            hora_inicio,
        ),
        estado=estado,
    )
    escenario["db"].add(turno)
    escenario["db"].commit()

    return turno


def datos_nuevo(
    escenario,
    hora_inicio,
    duracion=30,
):
    return TurnoCrear(
        paciente_id=escenario["paciente"].id,
        prestacion_id=escenario["prestaciones"][duracion].id,
        fecha_hora=datetime.combine(
            escenario["fecha"],
            hora_inicio,
        ),
    )


def test_rechaza_solapamiento_total(escenario_turnos):
    crear_existente(
        escenario_turnos,
        time(10, 0),
        duracion=60,
    )

    with pytest.raises(HTTPException) as error:
        crear_turno(
            escenario_turnos["db"],
            datos_nuevo(
                escenario_turnos,
                time(10, 15),
                duracion=30,
            ),
        )

    assert error.value.status_code == 409


def test_rechaza_solapamiento_parcial(escenario_turnos):
    crear_existente(
        escenario_turnos,
        time(10, 0),
        duracion=60,
    )

    with pytest.raises(HTTPException) as error:
        crear_turno(
            escenario_turnos["db"],
            datos_nuevo(
                escenario_turnos,
                time(9, 30),
                duracion=60,
            ),
        )

    assert error.value.status_code == 409


def test_permite_turnos_consecutivos(escenario_turnos):
    crear_existente(
        escenario_turnos,
        time(10, 0),
        duracion=30,
    )

    turno = crear_turno(
        escenario_turnos["db"],
        datos_nuevo(
            escenario_turnos,
            time(10, 30),
            duracion=30,
        ),
    )

    assert utc_a_zona_negocio(
        desde_base_utc(turno.fecha_hora),
    ).time() == time(10, 30)


def test_ignora_turnos_cancelados(escenario_turnos):
    crear_existente(
        escenario_turnos,
        time(10, 0),
        duracion=60,
        estado="cancelado",
    )

    turno = crear_turno(
        escenario_turnos["db"],
        datos_nuevo(
            escenario_turnos,
            time(10, 15),
            duracion=30,
        ),
    )

    assert utc_a_zona_negocio(
        desde_base_utc(turno.fecha_hora),
    ).time() == time(10, 15)


def test_reprogramacion_excluye_el_propio_turno(
    escenario_turnos,
):
    turno = crear_existente(
        escenario_turnos,
        time(10, 0),
        duracion=30,
    )

    reprogramado = reprogramar_turno(
        escenario_turnos["db"],
        turno.id,
        TurnoReprogramar(
            fecha_hora=turno.fecha_hora,
        ),
    )

    assert reprogramado.id == turno.id
    assert reprogramado.fecha_hora == turno.fecha_hora


def test_reprogramacion_conserva_deteccion_de_solapamientos(
    escenario_turnos,
):
    turno = crear_existente(
        escenario_turnos,
        time(9, 0),
        duracion=30,
    )
    crear_existente(
        escenario_turnos,
        time(10, 0),
        duracion=60,
    )

    with pytest.raises(HTTPException) as error:
        reprogramar_turno(
            escenario_turnos["db"],
            turno.id,
            TurnoReprogramar(
                fecha_hora=datetime.combine(
                    escenario_turnos["fecha"],
                    time(10, 30),
                ),
            ),
        )

    assert error.value.status_code == 409
