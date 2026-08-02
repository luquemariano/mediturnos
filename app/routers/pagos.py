from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from mercadopago.webhook import (
    InvalidWebhookSignatureError,
    WebhookSignatureValidator,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import obtener_db
from app.schemas.pago import PagoRespuesta
from app.services.pago_service import (
    crear_preferencia_pago,
    obtener_pago_por_turno,
    procesar_notificacion_pago,
)


router = APIRouter(
    prefix="/pagos",
    tags=["Pagos"],
)


@router.post(
    "/turnos/{turno_id}/preferencia",
    response_model=PagoRespuesta,
    status_code=201,
    summary="Crear preferencia de pago",
)
def crear_preferencia(
    turno_id: int,
    db: Session = Depends(obtener_db),
):
    return crear_preferencia_pago(
        db,
        turno_id,
    )


@router.get(
    "/turnos/{turno_id}",
    response_model=PagoRespuesta,
    summary="Consultar el pago de un turno",
)
def consultar_pago_turno(
    turno_id: int,
    db: Session = Depends(obtener_db),
):
    return obtener_pago_por_turno(
        db,
        turno_id,
    )


@router.post(
    "/webhook",
    status_code=200,
    summary="Recibir notificación de Mercado Pago",
)
async def recibir_webhook_mercado_pago(
    request: Request,
    db: Session = Depends(obtener_db),
) -> dict[str, Any]:
    x_signature = request.headers.get("x-signature")
    x_request_id = request.headers.get("x-request-id")
    data_id = request.query_params.get("data.id")

    if not settings.mercado_pago_webhook_secret:
        raise HTTPException(
            status_code=500,
            detail="El webhook de Mercado Pago no está configurado.",
        )

    try:
        WebhookSignatureValidator.validate(
            x_signature,
            x_request_id,
            data_id,
            settings.mercado_pago_webhook_secret,
        )

    except InvalidWebhookSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Firma de webhook inválida.",
        )

    body = await request.json()

    tipo_evento = body.get("type")

    if tipo_evento != "payment":
        return {
            "recibido": True,
            "procesado": False,
        }

    payment_id = (
        body.get("data", {}).get("id")
        or data_id
    )

    if payment_id is None:
        return {
            "recibido": True,
            "procesado": False,
        }

    pago = procesar_notificacion_pago(
        db,
        str(payment_id),
    )

    return {
        "recibido": True,
        "procesado": pago is not None,
    }