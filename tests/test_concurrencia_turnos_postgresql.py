import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time, timedelta
from decimal import Decimal
from threading import Barrier

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.core.datetime_utils import fecha_hora_civil_a_utc
from app.models.disponibilidad import Disponibilidad
from app.models.especialidad import Especialidad
from app.models.paciente import Paciente
from app.models.prestacion import Prestacion
from app.models.profesional import Profesional
from app.models.turno import Turno
from app.schemas.turno import (
    TurnoActualizarEstado,
    TurnoCrear,
    TurnoReprogramar,
)
from app.services import turno_service


POSTGRES_URL = os.getenv("TEST_POSTGRES_CONCURRENCY_URL")

pytestmark = pytest.mark.skipif(
    not POSTGRES_URL,
    reason=(
        "Requiere PostgreSQL real mediante "
        "TEST_POSTGRES_CONCURRENCY_URL."
    ),
)

engine_postgresql = (
    create_engine(POSTGRES_URL, pool_size=8)
    if POSTGRES_URL
    else None
)
SessionPostgresql = (
    sessionmaker(
        bind=engine_postgresql,
        expire_on_commit=False,
    )
    if engine_postgresql is not None
    else None
)


@pytest.fixture
def escenario_postgresql():
    with engine_postgresql.begin() as conexion:
        conexion.execute(
            text(
                "TRUNCATE TABLE turnos, disponibilidades, "
                "prestaciones, profesionales_especialidades, "
                "pacientes, profesionales, especialidades "
                "RESTART IDENTITY CASCADE"
            )
        )

    fecha = (datetime.now() + timedelta(days=7)).date()

    with SessionPostgresql() as db:
        pacientes = [
            Paciente(
                nombre="Ana",
                apellido="Paciente",
                dni=f"3000000{numero}",
                telefono="3515551234",
            )
            for numero in (1, 2)
        ]
        profesionales = [
            Profesional(
                nombre=f"Profesional {numero}",
                apellido="Concurrente",
                matricula=f"MP-CONC-{numero}",
            )
            for numero in (1, 2)
        ]
        especialidad = Especialidad(
            nombre="Clínica concurrente",
            duracion_turno_minutos=30,
        )
        db.add_all(
            [*pacientes, *profesionales, especialidad]
        )
        db.flush()

        prestaciones = {}

        for profesional in profesionales:
            for duracion in (30, 60):
                prestacion = Prestacion(
                    nombre=(
                        f"Consulta {profesional.id} "
                        f"de {duracion} minutos"
                    ),
                    duracion_minutos=duracion,
                    precio=Decimal("15000.00"),
                    modalidad="presencial",
                    profesional_id=profesional.id,
                    especialidad_id=especialidad.id,
                )
                db.add(prestacion)
                db.flush()
                prestaciones[
                    profesional.id,
                    duracion,
                ] = prestacion.id

            db.add(
                Disponibilidad(
                    profesional_id=profesional.id,
                    dia_semana=fecha.weekday(),
                    hora_inicio=time(8, 0),
                    hora_fin=time(18, 0),
                )
            )

        db.commit()

        escenario = {
            "fecha": fecha,
            "pacientes": [paciente.id for paciente in pacientes],
            "profesionales": [
                profesional.id
                for profesional in profesionales
            ],
            "prestaciones": prestaciones,
        }

    yield escenario

    with engine_postgresql.begin() as conexion:
        conexion.execute(
            text(
                "TRUNCATE TABLE turnos, disponibilidades, "
                "prestaciones, profesionales_especialidades, "
                "pacientes, profesionales, especialidades "
                "RESTART IDENTITY CASCADE"
            )
        )


def datos_turno(
    escenario,
    paciente_indice,
    profesional_indice,
    hora,
    duracion=30,
):
    profesional_id = escenario["profesionales"][
        profesional_indice
    ]

    return TurnoCrear(
        paciente_id=escenario["pacientes"][paciente_indice],
        prestacion_id=escenario["prestaciones"][
            profesional_id,
            duracion,
        ],
        fecha_hora=datetime.combine(
            escenario["fecha"],
            hora,
        ),
    )


def ejecutar_creacion(datos):
    with SessionPostgresql() as db:
        try:
            turno = turno_service.crear_turno(db, datos)
            return "creado", turno.id, db.execute(
                select(1)
            ).scalar_one()
        except HTTPException as error:
            sesion_reutilizable = db.execute(
                select(1)
            ).scalar_one()
            return (
                "conflicto",
                error.status_code,
                error.detail,
                sesion_reutilizable,
            )


def sincronizar_intento_reserva(monkeypatch):
    barrera = Barrier(2, timeout=10)
    bloquear_original = turno_service.bloquear_agenda_profesional

    def sincronizar_y_bloquear(*args, **kwargs):
        barrera.wait()
        return bloquear_original(*args, **kwargs)

    monkeypatch.setattr(
        turno_service,
        "bloquear_agenda_profesional",
        sincronizar_y_bloquear,
    )


def ejecutar_en_par(funcion_a, funcion_b):
    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        futuro_a = ejecutor.submit(funcion_a)
        futuro_b = ejecutor.submit(funcion_b)

        return futuro_a.result(), futuro_b.result()


def assert_un_creado_un_conflicto(resultados):
    estados = sorted(resultado[0] for resultado in resultados)

    assert estados == ["conflicto", "creado"]
    conflicto = next(
        resultado
        for resultado in resultados
        if resultado[0] == "conflicto"
    )
    assert conflicto[1:] == (
        409,
        "El horario ya no está disponible.",
        1,
    )


def test_dos_reservas_concurrentes_exactamente_iguales(
    escenario_postgresql,
    monkeypatch,
):
    sincronizar_intento_reserva(monkeypatch)
    datos_a = datos_turno(
        escenario_postgresql, 0, 0, time(10, 0)
    )
    datos_b = datos_turno(
        escenario_postgresql, 1, 0, time(10, 0)
    )

    resultados = ejecutar_en_par(
        lambda: ejecutar_creacion(datos_a),
        lambda: ejecutar_creacion(datos_b),
    )

    assert_un_creado_un_conflicto(resultados)

    with SessionPostgresql() as db:
        assert db.query(Turno).count() == 1


def test_solapamiento_parcial_concurrente(
    escenario_postgresql,
    monkeypatch,
):
    sincronizar_intento_reserva(monkeypatch)
    datos_a = datos_turno(
        escenario_postgresql,
        0,
        0,
        time(10, 0),
        duracion=60,
    )
    datos_b = datos_turno(
        escenario_postgresql,
        1,
        0,
        time(10, 30),
        duracion=60,
    )

    resultados = ejecutar_en_par(
        lambda: ejecutar_creacion(datos_a),
        lambda: ejecutar_creacion(datos_b),
    )

    assert_un_creado_un_conflicto(resultados)


def test_turnos_adyacentes_concurrentes(
    escenario_postgresql,
    monkeypatch,
):
    sincronizar_intento_reserva(monkeypatch)
    resultados = ejecutar_en_par(
        lambda: ejecutar_creacion(
            datos_turno(
                escenario_postgresql, 0, 0, time(10, 0)
            )
        ),
        lambda: ejecutar_creacion(
            datos_turno(
                escenario_postgresql, 1, 0, time(10, 30)
            )
        ),
    )

    assert [resultado[0] for resultado in resultados] == [
        "creado",
        "creado",
    ]


def test_reservas_concurrentes_profesionales_distintos(
    escenario_postgresql,
    monkeypatch,
):
    sincronizar_intento_reserva(monkeypatch)
    resultados = ejecutar_en_par(
        lambda: ejecutar_creacion(
            datos_turno(
                escenario_postgresql, 0, 0, time(10, 0)
            )
        ),
        lambda: ejecutar_creacion(
            datos_turno(
                escenario_postgresql, 1, 1, time(10, 0)
            )
        ),
    )

    assert [resultado[0] for resultado in resultados] == [
        "creado",
        "creado",
    ]


def test_creacion_contra_reprogramacion(
    escenario_postgresql,
    monkeypatch,
):
    with SessionPostgresql() as db:
        turno_original = turno_service.crear_turno(
            db,
            datos_turno(
                escenario_postgresql, 0, 0, time(9, 0)
            ),
        )
        turno_id = turno_original.id

    sincronizar_intento_reserva(monkeypatch)

    def reprogramar():
        with SessionPostgresql() as db:
            try:
                turno = turno_service.reprogramar_turno(
                    db,
                    turno_id,
                    TurnoReprogramar(
                        fecha_hora=datetime.combine(
                            escenario_postgresql["fecha"],
                            time(10, 0),
                        )
                    ),
                )
                return "creado", turno.id
            except HTTPException as error:
                assert db.execute(select(1)).scalar_one() == 1
                return (
                    "conflicto",
                    error.status_code,
                    error.detail,
                )

    resultados = ejecutar_en_par(
        lambda: ejecutar_creacion(
            datos_turno(
                escenario_postgresql, 1, 0, time(10, 0)
            )
        ),
        reprogramar,
    )

    assert sorted(resultado[0] for resultado in resultados) == [
        "conflicto",
        "creado",
    ]

    with SessionPostgresql() as db:
        turnos = db.query(Turno).all()

        for turno_a in turnos:
            for turno_b in turnos:
                if turno_a.id >= turno_b.id:
                    continue
                assert not (
                    turno_a.fecha_hora < turno_b.fecha_fin
                    and turno_a.fecha_fin > turno_b.fecha_hora
                )


def test_cancelado_permite_reutilizar_intervalo_y_no_reactivar(
    escenario_postgresql,
):
    with SessionPostgresql() as db:
        cancelado = turno_service.crear_turno(
            db,
            datos_turno(
                escenario_postgresql, 0, 0, time(10, 0)
            ),
        )
        turno_service.cambiar_estado_turno(
            db,
            cancelado.id,
            TurnoActualizarEstado(estado="cancelado"),
        )
        activo = turno_service.crear_turno(
            db,
            datos_turno(
                escenario_postgresql, 1, 0, time(10, 0)
            ),
        )

        with pytest.raises(HTTPException) as error:
            turno_service.cambiar_estado_turno(
                db,
                cancelado.id,
                TurnoActualizarEstado(estado="reservado"),
            )

        assert error.value.status_code == 409
        assert error.value.detail == (
            "El horario ya no está disponible."
        )
        assert db.execute(select(1)).scalar_one() == 1
        db.refresh(cancelado)
        assert cancelado.estado == "cancelado"
        assert activo.estado == "reservado"


def test_cambio_duracion_no_altera_fecha_fin_historica(
    escenario_postgresql,
):
    with SessionPostgresql() as db:
        turno = turno_service.crear_turno(
            db,
            datos_turno(
                escenario_postgresql, 0, 0, time(10, 0)
            ),
        )
        fecha_fin_original = turno.fecha_fin
        prestacion = db.get(Prestacion, turno.prestacion_id)
        prestacion.duracion_minutos = 120
        db.commit()
        db.refresh(turno)

        assert turno.fecha_fin == fecha_fin_original


def test_constraint_rechaza_solapamiento_directo(
    escenario_postgresql,
):
    profesional_id = escenario_postgresql["profesionales"][0]
    prestacion_id = escenario_postgresql["prestaciones"][
        profesional_id,
        60,
    ]
    inicio = fecha_hora_civil_a_utc(
        escenario_postgresql["fecha"],
        time(10, 0),
    )

    with SessionPostgresql() as db:
        turno_existente = Turno(
            paciente_id=escenario_postgresql["pacientes"][0],
            prestacion_id=prestacion_id,
            profesional_id=profesional_id,
            fecha_hora=inicio,
            fecha_fin=inicio + timedelta(minutes=60),
        )
        db.add(turno_existente)
        db.commit()
        turno_existente_id = turno_existente.id

        turno_solapado = Turno(
            paciente_id=escenario_postgresql["pacientes"][1],
            prestacion_id=prestacion_id,
            profesional_id=profesional_id,
            fecha_hora=inicio + timedelta(minutes=30),
            fecha_fin=inicio + timedelta(minutes=90),
        )
        db.add(turno_solapado)

        with pytest.raises(IntegrityError) as error:
            db.commit()

        assert error.value.orig.sqlstate == "23P01"
        assert error.value.orig.diag.constraint_name == (
            "ex_turnos_profesional_intervalo_activo"
        )

        db.rollback()

        assert db.execute(select(1)).scalar_one() == 1
        turnos = db.query(Turno).all()
        assert [turno.id for turno in turnos] == [
            turno_existente_id
        ]
