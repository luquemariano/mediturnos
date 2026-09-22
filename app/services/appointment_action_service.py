import logging
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.datetime_utils import desde_base_utc
from app.models.turno import Turno
from app.services.turno_service import aplicar_accion_turno_validado
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

    try:
        turno, result = aplicar_accion_turno_validado(db, turno, action)
    except HTTPException as error:
        if error.status_code == 409:
            raise AppointmentActionError("not_allowed") from error
        raise
    if result in {"confirm", "cancel"}:
        logger.info("appointment_action.%s", f"{action}ed" if action == "confirm" else "cancelled")
    return turno, result
