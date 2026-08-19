from datetime import UTC, date, datetime, time
import os
from zoneinfo import ZoneInfo

ZONA_NEGOCIO = ZoneInfo(os.getenv("APP_TIMEZONE", "America/Argentina/Buenos_Aires"))


def _zona_negocio() -> ZoneInfo:
    return ZONA_NEGOCIO


def ahora_utc() -> datetime:
    return datetime.now(UTC)


def ahora_negocio(zona: ZoneInfo | None = None) -> datetime:
    return ahora_utc().astimezone(zona or _zona_negocio())


def fecha_actual_negocio() -> date:
    return ahora_negocio().date()


def fecha_hora_civil_a_utc(
    fecha: date,
    hora: time,
) -> datetime:
    fecha_hora = datetime.combine(
        fecha,
        hora.replace(tzinfo=None),
        tzinfo=ZONA_NEGOCIO,
    )
    return fecha_hora.astimezone(UTC)


def utc_a_zona_negocio(fecha_hora: datetime, zona: ZoneInfo | None = None) -> datetime:
    if fecha_hora.tzinfo is None:
        raise ValueError("La fecha y hora UTC debe incluir zona horaria.")
    return fecha_hora.astimezone(zona or _zona_negocio())


def a_zona_negocio(fecha_hora: datetime) -> datetime:
    if fecha_hora.tzinfo is None:
        return fecha_hora.replace(tzinfo=ZONA_NEGOCIO)
    return fecha_hora.astimezone(ZONA_NEGOCIO)


def a_utc(fecha_hora: datetime) -> datetime:
    """Normaliza un instante a UTC; fechas ingenuas se consideran de negocio."""
    return a_zona_negocio(fecha_hora).astimezone(UTC)


def desde_base_utc(fecha_hora: datetime) -> datetime:
    """Normaliza resultados de BD; SQLite puede devolverlos sin tzinfo."""
    if fecha_hora.tzinfo is None:
        return fecha_hora.replace(tzinfo=UTC)
    return fecha_hora.astimezone(UTC)
