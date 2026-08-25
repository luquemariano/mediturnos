import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.datetime_utils import desde_base_utc
from app.models.turno import Turno
from app.services.appointment_action_token_service import (
    AppointmentActionTokenError,
    verify_appointment_action_token,
)

logger = logging.getLogger("mediturnos.appointment_action")


class AppointmentActionError(ValueError):
    pass


def apply_appointment_action(db: Session, *, token: str, secret: str, action: str, now: datetime | None = None) -> tuple[Turno, str]:
    try:
        payload = verify_appointment_action_token(token=token, secret=secret, expected_scope=action, now=now)
    except AppointmentActionTokenError as error:
        logger.info("appointment_action.%s", error.args[0])
        raise AppointmentActionError(error.args[0]) from error

    turno = db.query(Turno).with_for_update().filter(Turno.id == int(payload["turno_id"])).one_or_none()
    if turno is None:
        raise AppointmentActionError("not_found")
    current = now or datetime.now(UTC)
    if desde_base_utc(turno.fecha_hora) != desde_base_utc(datetime.fromisoformat(payload["snapshot"])):
        logger.info("appointment_action.rescheduled")
        raise AppointmentActionError("rescheduled")
    if desde_base_utc(turno.fecha_hora) <= current:
        raise AppointmentActionError("passed")

    if action == "confirm":
        if turno.estado == "confirmado":
            return turno, "already_confirmed"
        if turno.estado != "reservado":
            raise AppointmentActionError("not_allowed")
        turno.estado = "confirmado"
    else:
        if turno.estado == "cancelado":
            return turno, "already_cancelled"
        if turno.estado not in {"reservado", "confirmado"}:
            raise AppointmentActionError("not_allowed")
        turno.estado = "cancelado"
    db.commit()
    logger.info("appointment_action.%s", f"{action}ed" if action == "confirm" else "cancelled")
    return turno, action
