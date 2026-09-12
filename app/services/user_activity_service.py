from sqlalchemy.orm import Session

from app.models.user_activity_event import UserActivityEvent


def registrar_evento_actividad(
    db: Session,
    usuario_id: int,
    event_type: str,
    profesional_id: int | None = None,
    cuenta_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
) -> UserActivityEvent:
    evento = UserActivityEvent(
        usuario_id=usuario_id,
        profesional_id=profesional_id,
        cuenta_id=cuenta_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    db.add(evento)
    return evento
