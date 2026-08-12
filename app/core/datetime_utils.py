from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from app.core.config import settings


ZONA_NEGOCIO = ZoneInfo(settings.app_timezone)


def ahora_utc() -> datetime:
    return datetime.now(UTC)


def ahora_negocio() -> datetime:
    return ahora_utc().astimezone(ZONA_NEGOCIO)


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


def utc_a_zona_negocio(fecha_hora: datetime) -> datetime:
    if fecha_hora.tzinfo is None:
        raise ValueError("La fecha y hora UTC debe incluir zona horaria.")
    return fecha_hora.astimezone(ZONA_NEGOCIO)


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
