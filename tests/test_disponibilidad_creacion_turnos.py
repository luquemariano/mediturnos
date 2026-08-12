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
from app.services.disponibilidad_service import obtener_horarios_libres
from tests.conftest import SessionTest


@pytest.fixture
def escenario_disponibilidad():
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
        matricula="MP-DISP-001",
    )
    especialidad = Especialidad(
        nombre="Clínica Médica",
        duracion_turno_minutos=30,
    )
    db.add_all([paciente, profesional, especialidad])
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

    db.add(
        Disponibilidad(
            profesional_id=profesional.id,
            dia_semana=fecha.weekday(),
            hora_inicio=time(9, 0),
            hora_fin=time(12, 0),
            activa=True,
        )
    )
    db.commit()

    yield {
        "db": db,
        "fecha": fecha,
        "paciente_id": paciente.id,
        "prestacion_id": prestacion.id,
    }

    db.close()


def crear_en_horario(
    escenario,
    hora_inicio,
):
    return crear_turno(
        escenario["db"],
        TurnoCrear(
            paciente_id=escenario["paciente_id"],
            prestacion_id=escenario["prestacion_id"],
            fecha_hora=datetime.combine(
                escenario["fecha"],
                hora_inicio,
            ),
        ),
    )


def reprogramar_en_horario(
    escenario,
    hora_inicio,
):
    turno = Turno(
        paciente_id=escenario["paciente_id"],
        prestacion_id=escenario["prestacion_id"],
        fecha_hora=fecha_hora_civil_a_utc(
            escenario["fecha"],
            time(10, 0),
        ),
    )
    escenario["db"].add(turno)
    escenario["db"].commit()

    return reprogramar_turno(
        escenario["db"],
        turno.id,
        TurnoReprogramar(
            fecha_hora=datetime.combine(
                escenario["fecha"],
                hora_inicio,
            ),
        ),
    )


def test_permite_inicio_exacto_de_disponibilidad(
    escenario_disponibilidad,
):
    turno = crear_en_horario(
        escenario_disponibilidad,
        time(9, 0),
    )

    assert utc_a_zona_negocio(
        desde_base_utc(turno.fecha_hora),
    ).time() == time(9, 0)


def test_horarios_libres_excluye_el_propio_turno(
    escenario_disponibilidad,
):
    turno = crear_en_horario(
        escenario_disponibilidad,
        time(9, 0),
    )

    horarios_sin_exclusion = obtener_horarios_libres(
        escenario_disponibilidad["db"],
        escenario_disponibilidad["prestacion_id"],
        escenario_disponibilidad["fecha"],
    )
    horarios_con_exclusion = obtener_horarios_libres(
        escenario_disponibilidad["db"],
        escenario_disponibilidad["prestacion_id"],
        escenario_disponibilidad["fecha"],
        turno.id,
    )

    horas_sin_exclusion = {
        utc_a_zona_negocio(item["fecha_hora"]).time()
        for item in horarios_sin_exclusion
    }
    horas_con_exclusion = {
        utc_a_zona_negocio(item["fecha_hora"]).time()
        for item in horarios_con_exclusion
    }

    assert time(9, 0) not in horas_sin_exclusion
    assert time(9, 0) in horas_con_exclusion


def test_rechaza_exclusion_con_prestacion_incorrecta(
    escenario_disponibilidad,
):
    turno = crear_en_horario(
        escenario_disponibilidad,
        time(9, 0),
    )
    db = escenario_disponibilidad["db"]
    prestacion_original = db.get(
        Prestacion,
        escenario_disponibilidad["prestacion_id"],
    )
    otra_prestacion = Prestacion(
        nombre="Otra consulta",
        duracion_minutos=30,
        precio=Decimal("15000.00"),
        modalidad="presencial",
        profesional_id=prestacion_original.profesional_id,
        especialidad_id=prestacion_original.especialidad_id,
    )
    db.add(otra_prestacion)
    db.commit()

    with pytest.raises(HTTPException) as error:
        obtener_horarios_libres(
            db,
            otra_prestacion.id,
            escenario_disponibilidad["fecha"],
            turno.id,
        )

    assert error.value.status_code == 400
    assert error.value.detail == (
        "El turno no corresponde a la prestación solicitada."
    )


@pytest.mark.parametrize("estado", ["cancelado", "finalizado"])
def test_rechaza_exclusion_de_turno_no_reprogramable(
    escenario_disponibilidad,
    estado,
):
    turno = crear_en_horario(
        escenario_disponibilidad,
        time(9, 0),
    )
    turno.estado = estado
    escenario_disponibilidad["db"].commit()

    with pytest.raises(HTTPException) as error:
        obtener_horarios_libres(
            escenario_disponibilidad["db"],
            escenario_disponibilidad["prestacion_id"],
            escenario_disponibilidad["fecha"],
            turno.id,
        )

    assert error.value.status_code == 400
    assert error.value.detail == (
        "No se puede excluir un turno cancelado o finalizado."
    )


def test_permite_fin_exacto_de_disponibilidad(
    escenario_disponibilidad,
):
    turno = crear_en_horario(
        escenario_disponibilidad,
        time(11, 30),
    )

    assert utc_a_zona_negocio(
        desde_base_utc(turno.fecha_hora),
    ).time() == time(11, 30)


def test_rechaza_inicio_anterior_a_disponibilidad(
    escenario_disponibilidad,
):
    with pytest.raises(HTTPException) as error:
        crear_en_horario(
            escenario_disponibilidad,
            time(8, 45),
        )

    assert error.value.status_code == 409


def test_rechaza_fin_posterior_a_disponibilidad(
    escenario_disponibilidad,
):
    with pytest.raises(HTTPException) as error:
        crear_en_horario(
            escenario_disponibilidad,
            time(11, 45),
        )

    assert error.value.status_code == 409


def test_ignora_disponibilidad_inactiva(
    escenario_disponibilidad,
):
    db = escenario_disponibilidad["db"]
    disponibilidad = db.query(Disponibilidad).one()
    disponibilidad.activa = False
    db.commit()

    with pytest.raises(HTTPException) as error:
        crear_en_horario(
            escenario_disponibilidad,
            time(10, 0),
        )

    assert error.value.status_code == 409


@pytest.mark.parametrize(
    "hora_inicio",
    [
        time(9, 0),
        time(9, 15),
        time(11, 30),
    ],
)
def test_reprogramacion_acepta_mismos_limites_que_creacion(
    escenario_disponibilidad,
    hora_inicio,
):
    turno = reprogramar_en_horario(
        escenario_disponibilidad,
        hora_inicio,
    )

    assert utc_a_zona_negocio(
        desde_base_utc(turno.fecha_hora),
    ).time() == hora_inicio


@pytest.mark.parametrize(
    "hora_inicio",
    [
        time(8, 45),
        time(11, 45),
    ],
)
def test_reprogramacion_rechaza_mismos_limites_que_creacion(
    escenario_disponibilidad,
    hora_inicio,
):
    with pytest.raises(HTTPException) as error:
        reprogramar_en_horario(
            escenario_disponibilidad,
            hora_inicio,
        )

    assert error.value.status_code == 409


def test_reprogramacion_ignora_disponibilidad_inactiva(
    escenario_disponibilidad,
):
    db = escenario_disponibilidad["db"]
    disponibilidad = db.query(Disponibilidad).one()
    disponibilidad.activa = False
    db.commit()

    with pytest.raises(HTTPException) as error:
        reprogramar_en_horario(
            escenario_disponibilidad,
            time(10, 0),
        )

    assert error.value.status_code == 409
