from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from mercadopago.webhook import InvalidWebhookSignatureError, WebhookSignatureValidator
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import obtener_usuario_actual
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.suscripcion import (
    IniciarSuscripcionEntrada,
    IniciarSuscripcionRespuesta,
    OperacionSuscripcionRespuesta,
    SuscripcionRespuesta,
)
from app.services.suscripcion_mercadopago_service import (
    cancelar_suscripcion,
    iniciar_suscripcion,
    obtener_estado_suscripcion,
    procesar_webhook_suscripcion,
    sincronizar_suscripcion,
)


router = APIRouter(prefix="/cuentas", tags=["Suscripciones SaaS"])
webhook_router = APIRouter(prefix="/webhooks/mercadopago", tags=["Webhooks SaaS"])


@router.post("/{cuenta_id}/suscripcion/mercadopago/iniciar", response_model=IniciarSuscripcionRespuesta, status_code=201)
def iniciar(cuenta_id: int, entrada: IniciarSuscripcionEntrada, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return iniciar_suscripcion(
        db,
        cuenta_id,
        usuario,
        entrada.plan,
        entrada.card_token_id.get_secret_value(),
    )


@router.get("/{cuenta_id}/suscripcion", response_model=SuscripcionRespuesta)
def consultar(cuenta_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return obtener_estado_suscripcion(db, cuenta_id, usuario)


@router.post("/{cuenta_id}/suscripcion/mercadopago/sincronizar", response_model=OperacionSuscripcionRespuesta)
def sincronizar(cuenta_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return sincronizar_suscripcion(db, cuenta_id, usuario)


@router.post("/{cuenta_id}/suscripcion/mercadopago/cancelar", response_model=OperacionSuscripcionRespuesta)
def cancelar(cuenta_id: int, db: Session = Depends(obtener_db), usuario: Usuario = Depends(obtener_usuario_actual)):
    return cancelar_suscripcion(db, cuenta_id, usuario)


@webhook_router.post("/suscripciones", status_code=200)
async def webhook(request: Request, db: Session = Depends(obtener_db)) -> dict[str, Any]:
    signature = request.headers.get("x-signature")
    request_id = request.headers.get("x-request-id")
    data_id = request.query_params.get("data.id")
    secreto = settings.mercadopago_webhook_secret
    if secreto is None or not secreto.get_secret_value().strip():
        raise HTTPException(status_code=500, detail="El webhook de suscripciones no está configurado.")
    try:
        WebhookSignatureValidator.validate(signature, request_id, data_id, secreto.get_secret_value())
    except InvalidWebhookSignatureError as error:
        raise HTTPException(status_code=401, detail="Firma de webhook inválida.") from error
    body = await request.json()
    body_id = body.get("data", {}).get("id")
    if data_id is None:
        raise HTTPException(status_code=400, detail="Falta el identificador firmado.")
    if body_id is not None and str(body_id) != str(data_id):
        raise HTTPException(status_code=400, detail="El identificador firmado no coincide con el cuerpo.")
    topic = body.get("type") or body.get("topic")
    if topic not in {
        "subscription_preapproval", "subscription_preapproval_plan",
        "subscription_authorized_payment", "payment",
    }:
        return {"recibido": True, "procesado": False}
    procesado = procesar_webhook_suscripcion(
        db, topic=topic, resource_id=str(data_id), request_id=request_id,
        action=body.get("action"), payload=body,
    )
    return {"recibido": True, "procesado": procesado}
