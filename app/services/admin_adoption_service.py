from datetime import UTC, datetime

from sqlalchemy import case, distinct, func
from sqlalchemy.orm import Session

from app.models.profesional import Profesional
from app.models.user_activity_event import UserActivityEvent
from app.models.usuario import Usuario


EVENT_TYPES = {
    "patients_created": "patient_created",
    "appointments_created": "appointment_created",
    "services_created": "service_created",
    "availabilities_created": "availability_created",
    "clinical_evolutions_created": "clinical_evolution_created",
}


def _days_since(value: datetime | None, now: datetime) -> int | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return max(0, (now - value.astimezone(UTC)).days)


def _status(row: dict, days: int | None) -> str:
    if row["event_count"] == 0:
        return "sin_uso"
    if row["patients_created"] == 0 or row["appointments_created"] == 0:
        return "configurando"
    if days is not None and days <= 7:
        return "activo"
    if days is not None and days <= 15:
        return "en_riesgo"
    if days is not None and days > 15:
        return "inactivo"
    # Con eventos funcionales, last_activity_at siempre existe. Esta rama es
    # defensiva para datos inconsistentes y no expone un estado adicional.
    return "inactivo"


def obtener_adopcion_admin(
    db: Session,
    status: str | None = None,
    cuenta_id: int | None = None,
    q: str | None = None,
) -> list[dict]:
    if db.bind.dialect.name == "postgresql":
        active_date = func.date(func.timezone("UTC", UserActivityEvent.created_at))
    else:
        active_date = func.date(UserActivityEvent.created_at)
    event_count = func.count(UserActivityEvent.id).label("event_count")
    aggregates = (
        db.query(
            UserActivityEvent.profesional_id.label("profesional_id"),
            event_count,
            func.max(UserActivityEvent.created_at).label("last_activity_at"),
            func.count(distinct(active_date)).label("active_days"),
            *[
                func.sum(case((UserActivityEvent.event_type == event_type, 1), else_=0)).label(field)
                for field, event_type in EVENT_TYPES.items()
            ],
        )
        .group_by(UserActivityEvent.profesional_id)
        .subquery()
    )

    aggregate_columns = (
        aggregates.c.event_count,
        aggregates.c.last_activity_at,
        aggregates.c.active_days,
        aggregates.c.patients_created,
        aggregates.c.appointments_created,
        aggregates.c.services_created,
        aggregates.c.availabilities_created,
        aggregates.c.clinical_evolutions_created,
    )
    query = (
        db.query(Usuario, Profesional, *aggregate_columns)
        .join(Profesional, Profesional.usuario_id == Usuario.id)
        .outerjoin(aggregates, aggregates.c.profesional_id == Profesional.id)
        .filter(Usuario.rol == "profesional")
        .order_by(Profesional.apellido, Profesional.nombre, Profesional.id)
    )
    if cuenta_id is not None:
        query = query.filter(Profesional.cuenta_id == cuenta_id)
    if q:
        patron = f"%{q.strip()}%"
        query = query.filter(
            Usuario.email.ilike(patron)
            | Profesional.nombre.ilike(patron)
            | Profesional.apellido.ilike(patron)
        )

    now = datetime.now(UTC)
    resultado = []
    for (
        usuario,
        profesional,
        event_count_value,
        last_activity_at,
        active_days,
        patients_created,
        appointments_created,
        services_created,
        availabilities_created,
        clinical_evolutions_created,
    ) in query.all():
        data = {
            "usuario_id": usuario.id,
            "profesional_id": profesional.id,
            "cuenta_id": profesional.cuenta_id,
            "nombre": profesional.nombre,
            "apellido": profesional.apellido,
            "email": usuario.email,
            "first_login_at": usuario.first_login_at,
            "last_login_at": usuario.last_login_at,
            "login_count": usuario.login_count,
            "last_activity_at": last_activity_at,
            "active_days": active_days or 0,
            "patients_created": patients_created or 0,
            "appointments_created": appointments_created or 0,
            "services_created": services_created or 0,
            "availabilities_created": availabilities_created or 0,
            "clinical_evolutions_created": clinical_evolutions_created or 0,
        }
        data["days_since_last_activity"] = _days_since(data["last_activity_at"], now)
        data["adoption_status"] = _status(
            {**data, "event_count": event_count_value or 0},
            data["days_since_last_activity"],
        )
        if status is None or data["adoption_status"] == status:
            resultado.append(data)
    return resultado
