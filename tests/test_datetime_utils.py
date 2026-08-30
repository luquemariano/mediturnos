from datetime import UTC, date, datetime, time

from app.core.datetime_utils import (
    ZONA_NEGOCIO,
    a_utc,
    fecha_hora_civil_a_utc,
    rango_fechas_negocio_a_utc,
    utc_a_zona_negocio,
)
from app.schemas.turno import TurnoRespuesta


def test_convierte_hora_civil_argentina_a_utc():
    resultado = fecha_hora_civil_a_utc(
        date(2026, 8, 15),
        time(23, 30),
    )
    assert resultado == datetime(
        2026,
        8,
        16,
        2,
        30,
        tzinfo=UTC,
    )


def test_rango_civil_usa_fin_exclusivo_del_dia_siguiente():
    inicio, fin = rango_fechas_negocio_a_utc(date(2026, 8, 31), date(2026, 9, 6))
    assert inicio == datetime(2026, 8, 31, 3, 0, tzinfo=UTC)
    assert fin == datetime(2026, 9, 7, 3, 0, tzinfo=UTC)

def test_convierte_utc_a_dia_anterior_en_buenos_aires():
    resultado = utc_a_zona_negocio(
        datetime(2026, 8, 16, 2, 30, tzinfo=UTC),
    )

    assert resultado.date() == date(2026, 8, 15)
    assert resultado.time().replace(tzinfo=None) == time(23, 30)
    assert resultado.tzinfo == ZONA_NEGOCIO


def test_normaliza_entrada_ingenua_como_hora_de_negocio_a_utc():
    existente = datetime(2026, 8, 15, 9, 0)

    consciente = a_utc(existente)

    assert consciente == datetime(2026, 8, 15, 12, 0, tzinfo=UTC)


def test_serializa_turno_desde_base_como_utc():
    respuesta = TurnoRespuesta(
        id=1,
        paciente_id=1,
        paciente_nombre="Paciente Demo",
        prestacion_id=1,
        prestacion_nombre="Consulta",
        profesional_nombre="Profesional Demo",
        especialidad_nombre="Clínica",
        fecha_hora=datetime(2026, 8, 16, 2, 30),
        estado="reservado",
        observaciones=None,
    )

    assert respuesta.fecha_hora.isoformat() == (
        "2026-08-16T02:30:00+00:00"
    )
