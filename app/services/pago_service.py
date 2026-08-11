from decimal import Decimal

import mercadopago
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.pago import Pago
from app.models.turno import Turno
from app.models.usuario import Usuario
from app.repositories.pago_repository import (
    actualizar_pago_desde_mercado_pago,
    buscar_pago_por_turno,
    buscar_turno_por_id,
    crear_pago_pendiente,
    guardar_datos_preferencia,
)


def validar_acceso_pago(
    db: Session,
    turno_id: int,
    usuario_actual: Usuario,
) -> Turno:
    turno = buscar_turno_por_id(
        db,
        turno_id,
    )

    if turno is None:
        raise HTTPException(
            status_code=404,
            detail="Turno no encontrado.",
        )

    if usuario_actual.rol in {
        "administrador",
        "recepcionista",
    }:
        return turno

    if (
        usuario_actual.rol != "paciente"
        or turno.paciente.usuario_id != usuario_actual.id
    ):
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para operar sobre este pago.",
        )

    return turno


def crear_preferencia_pago(
    db: Session,
    turno_id: int,
    usuario_actual: Usuario,
) -> Pago:
    turno = validar_acceso_pago(
        db,
        turno_id,
        usuario_actual,
    )

    if turno.estado in {"cancelado", "finalizado"}:
        raise HTTPException(
            status_code=400,
            detail="El turno no admite pagos.",
        )

    pago_existente = buscar_pago_por_turno(
        db,
        turno_id,
    )

    if pago_existente is not None:
        if pago_existente.estado == "approved":
            raise HTTPException(
                status_code=409,
                detail="El turno ya se encuentra pagado.",
            )

        if (
            pago_existente.estado == "pendiente"
            and pago_existente.preference_id is not None
            and pago_existente.init_point is not None
        ):
            return pago_existente

    access_token = settings.mercado_pago_access_token

    if not access_token:
        raise HTTPException(
            status_code=500,
            detail="Mercado Pago no está configurado.",
        )

    monto = Decimal(
        str(turno.prestacion.precio)
    )

    pago = crear_pago_pendiente(
        db,
        turno_id,
        monto,
    )

    sdk = mercadopago.SDK(access_token)

    preference_data = {
        "items": [
            {
                "title": turno.prestacion.nombre,
                "quantity": 1,
                "unit_price": float(monto),
                "currency_id": "ARS",
            }
        ],
        "external_reference": str(turno.id),
    }

    respuesta = sdk.preference().create(
        preference_data
    )

    if respuesta["status"] not in {200, 201}:
        db.rollback()

        raise HTTPException(
            status_code=502,
            detail="Mercado Pago no pudo crear la preferencia.",
        )

    preference = respuesta["response"]

    guardar_datos_preferencia(
        pago,
        preference["id"],
        preference["init_point"],
    )

    db.commit()
    db.refresh(pago)

    return pago


def procesar_notificacion_pago(
    db: Session,
    payment_id: str,
) -> Pago | None:
    access_token = settings.mercado_pago_access_token

    if not access_token:
        raise HTTPException(
            status_code=500,
            detail="Mercado Pago no está configurado.",
        )

    sdk = mercadopago.SDK(access_token)

    respuesta = sdk.payment().get(
        payment_id,
    )

    if respuesta["status"] != 200:
        raise HTTPException(
            status_code=502,
            detail="No se pudo consultar el pago en Mercado Pago.",
        )

    datos_pago = respuesta["response"]

    external_reference = datos_pago.get(
        "external_reference"
    )

    if not external_reference:
        return None

    try:
        turno_id = int(external_reference)
    except ValueError:
        return None

    pago = buscar_pago_por_turno(
        db,
        turno_id,
    )

    if pago is None:
        return None

    estado = datos_pago["status"]

    actualizar_pago_desde_mercado_pago(
        pago,
        str(datos_pago["id"]),
        estado,
    )

    if estado == "approved":
        pago.turno.estado = "confirmado"

    elif estado in {
        "rejected",
        "cancelled",
        "refunded",
        "charged_back",
    }:
        pago.turno.estado = "cancelado"

    db.commit()
    db.refresh(pago)

    return pago


def obtener_pago_por_turno(
    db: Session,
    turno_id: int,
    usuario_actual: Usuario,
) -> Pago:
    validar_acceso_pago(
        db,
        turno_id,
        usuario_actual,
    )

    pago = buscar_pago_por_turno(
        db,
        turno_id,
    )

    if pago is None:
        raise HTTPException(
            status_code=404,
            detail="No se encontró un pago para el turno.",
        )

    return pago
