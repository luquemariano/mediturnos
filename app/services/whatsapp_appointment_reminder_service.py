from dataclasses import dataclass
from datetime import UTC, datetime
from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.core.datetime_utils import desde_base_utc, utc_a_zona_negocio
from app.integrations.messaging import (
    DEFAULT_TEMPLATE_MAPPING,
    OutboundMessage,
    MessagingProvider,
    get_messaging_provider,
)
from app.models.message_delivery import MessageDelivery
from app.models.turno import Turno
from app.services.appointment_action_token_service import generate_appointment_action_token
from app.services.message_delivery_service import (
    claim_pending,
    create_delivery,
    get_delivery_by_idempotency_key,
    mark_failed,
    mark_sent,
)
from app.services.phone_service import get_whatsapp_recipient


ESTADOS_NOTIFICABLES = {"reservado", "confirmado"}


@dataclass(frozen=True)
class WhatsAppReminderResult:
    status: str
    delivery_id: int | None = None
    sent: bool = False
    reason: str | None = None


def _config_value(config, name: str):
    if config is not None:
        return getattr(config, name)
    from app.core.config import settings

    return getattr(settings, name)


def _idempotency_key(turno: Turno, snapshot: datetime) -> str:
    return f"appointment-reminder:{turno.id}:{snapshot.isoformat()}:whatsapp:v1"


def _outbound_message(turno: Turno, recipient: str, confirm_token: str, cancel_token: str) -> OutboundMessage:
    return OutboundMessage(
        channel="whatsapp",
        recipient=recipient,
        message_type="appointment_reminder_v2",
        payload={
            "appointment_datetime": utc_a_zona_negocio(desde_base_utc(turno.fecha_hora)).strftime("%d/%m/%Y %H:%M"),
            "professional_name": f"{turno.profesional.nombre} {turno.profesional.apellido}",
            "confirm_token": confirm_token,
            "cancel_token": cancel_token,
        },
    )


def send_whatsapp_appointment_reminder(
    db: Session,
    turno_id: int,
    *,
    provider: MessagingProvider | None = None,
    config=None,
    ahora: datetime | None = None,
) -> WhatsAppReminderResult:
    if not _config_value(config, "whatsapp_enabled"):
        return WhatsAppReminderResult("feature_disabled", reason="whatsapp_disabled")
    turno = db.get(Turno, turno_id)
    if turno is None:
        return WhatsAppReminderResult("not_eligible", reason="appointment_not_found")
    if turno.estado not in ESTADOS_NOTIFICABLES:
        return WhatsAppReminderResult("not_eligible", reason="appointment_unavailable")
    recipient = get_whatsapp_recipient(turno.paciente)
    if recipient is None:
        return WhatsAppReminderResult("not_eligible", reason="recipient_not_eligible")

    snapshot = desde_base_utc(turno.fecha_hora)
    key = _idempotency_key(turno, snapshot)
    existing = get_delivery_by_idempotency_key(db, key)
    if existing is not None:
        if existing.status == "sent":
            return WhatsAppReminderResult("already_sent", existing.id, True)
        if existing.status in {"processing", "failed"}:
            return WhatsAppReminderResult(existing.status, existing.id, False)
        delivery = existing
    else:
        delivery = create_delivery(
            db,
            channel="whatsapp",
            purpose="appointment_reminder",
            message_type="appointment_reminder_v2",
            recipient_snapshot=recipient,
            idempotency_key=key,
        )
    db.commit()
    claimed = claim_pending(db, ahora or datetime.now(UTC), limite=1)
    db.commit()
    if not claimed or claimed[0].id != delivery.id:
        return WhatsAppReminderResult("processing", delivery.id, False)

    secret = _config_value(config, "appointment_action_secret")
    secret_value = secret.get_secret_value() if hasattr(secret, "get_secret_value") else str(secret)
    confirm_token = generate_appointment_action_token(
        secret=secret_value, turno_id=turno.id, appointment_datetime_snapshot=snapshot, action_scope="confirm"
    )
    cancel_token = generate_appointment_action_token(
        secret=secret_value, turno_id=turno.id, appointment_datetime_snapshot=snapshot, action_scope="cancel"
    )
    message = _outbound_message(
        turno,
        recipient,
        confirm_token,
        cancel_token,
    )
    selected_provider = provider
    if selected_provider is None:
        provider_name = _config_value(config, "whatsapp_provider")
        if provider_name == "meta":
            selected_provider = get_messaging_provider(
                provider_name,
                api_version=_config_value(config, "whatsapp_api_version"),
                phone_number_id=_config_value(config, "whatsapp_phone_number_id"),
                access_token=_config_value(config, "whatsapp_access_token"),
                template_mapping=DEFAULT_TEMPLATE_MAPPING,
            )
        else:
            selected_provider = get_messaging_provider(provider_name)
    try:
        result = selected_provider.send(message)
    except Exception as error:
        mark_failed(db, delivery, str(error))
        db.commit()
        return WhatsAppReminderResult("failed", delivery.id, False, "provider_error")
    mark_sent(db, delivery, provider=result.provider, provider_message_id=result.provider_message_id, ahora=ahora)
    db.commit()
    return WhatsAppReminderResult("sent", delivery.id, True)
