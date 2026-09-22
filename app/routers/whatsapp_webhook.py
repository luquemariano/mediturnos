import json

from fastapi import APIRouter, HTTPException, Query, Request, Response

from app.core.config import settings
from app.services.whatsapp_webhook_service import parse_webhook_events, verify_webhook_signature


router = APIRouter(prefix="/webhooks/whatsapp", tags=["WhatsApp webhook"])


def _enabled() -> None:
    if not settings.whatsapp_enabled:
        raise HTTPException(status_code=404, detail="Recurso no encontrado.")


@router.get("")
def verify(
    mode: str | None = Query(default=None, alias="hub.mode"),
    verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> Response:
    _enabled()
    if mode is None or verify_token is None or challenge is None:
        raise HTTPException(status_code=400, detail="Faltan parámetros de verificación.")
    configured = settings.whatsapp_verify_token.get_secret_value() if settings.whatsapp_verify_token else ""
    if mode != "subscribe" or not hmac_compare(verify_token, configured):
        raise HTTPException(status_code=403, detail="Verificación inválida.")
    return Response(content=challenge, media_type="text/plain")


def hmac_compare(left: str, right: str) -> bool:
    import hmac
    return bool(right) and hmac.compare_digest(left, right)


@router.post("")
async def receive(request: Request) -> dict[str, bool | int]:
    _enabled()
    secret = settings.whatsapp_app_secret.get_secret_value() if settings.whatsapp_app_secret else ""
    raw_body = await request.body()
    if not verify_webhook_signature(raw_body, request.headers.get("x-hub-signature-256"), secret):
        raise HTTPException(status_code=401, detail="Firma inválida.")
    try:
        payload = json.loads(raw_body)
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=400, detail="Cuerpo inválido.") from error
    events = parse_webhook_events(payload)
    return {"received": True, "events": len(events)}
