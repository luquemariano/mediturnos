from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import obtener_usuario_actual
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.notification import NotificationListResponse, NotificationResponse
from app.services.notification_service import list_notifications, mark_notification_read

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListResponse)
def notifications(db: Session = Depends(obtener_db), user: Usuario = Depends(obtener_usuario_actual)):
    items, unread = list_notifications(db, user.id)
    return {"items": items, "unread_count": unread}


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def read_notification(notification_id: int, db: Session = Depends(obtener_db), user: Usuario = Depends(obtener_usuario_actual)):
    item = mark_notification_read(db, user.id, notification_id)
    if item is None:
        raise HTTPException(404, "Notificación no encontrada.")
    return item
