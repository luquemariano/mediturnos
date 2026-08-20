import hashlib
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.datetime_utils import ahora_utc, desde_base_utc
from app.models.cobro_suscripcion import CobroSuscripcion
from app.models.evento_suscripcion import EventoSuscripcion
from app.models.notificacion_mercadopago_suscripcion import NotificacionMercadoPagoSuscripcion
from app.models.suscripcion import Suscripcion
from app.models.usuario import Usuario
from app.repositories.suscripcion_repository import (
    obtener_cobro,
    obtener_cobro_por_payment,
    obtener_cuenta,
    obtener_membresia,
    obtener_notificacion,
    obtener_plan,
    obtener_suscripcion,
    obtener_suscripcion_por_preapproval,
)
from app.schemas.suscripcion import (
    IniciarSuscripcionRespuesta,
    OperacionSuscripcionRespuesta,
    SuscripcionRespuesta,
)
from app.services.cuenta_service import estado_efectivo
from app.services.mercadopago_subscription_service import (
    MercadoPagoSubscriptionError,
    MercadoPagoSubscriptionService,
)


PRECIOS_PLANES: dict[str, Decimal] = {
    "profesional": Decimal("34900.00"),
    "consultorio": Decimal("69900.00"),
    "centro": Decimal("149900.00"),
}
MONEDA = "ARS"
logger = logging.getLogger("turnelia.mercadopago.suscripciones")


def _registrar_error_proveedor(
    error: MercadoPagoSubscriptionError,
) -> None:
    if settings.app_env != "development":
        return
    respuesta = error.provider_response
    detalle = {
        "http_status": error.status_code,
        "operation": error.operation,
        "message": respuesta.get("message")
        if isinstance(respuesta, dict) else None,
        "error": respuesta.get("error")
        if isinstance(respuesta, dict) else None,
        "cause": respuesta.get("cause")
        if isinstance(respuesta, dict) else None,
        "provider_response": respuesta,
    }
    logger.warning(
        "Mercado Pago rechazó una operación de suscripción: %s",
        json.dumps(detalle, ensure_ascii=False, default=str),
    )


def _gateway() -> MercadoPagoSubscriptionService:
    token = settings.mercadopago_access_token
    if token is None or not token.get_secret_value().strip():
        raise HTTPException(status_code=503, detail="La facturación por Mercado Pago no está configurada.")
    return MercadoPagoSubscriptionService(token.get_secret_value())


def _payer_email(usuario: Usuario) -> str:
    if settings.mercadopago_env != "sandbox":
        return usuario.email
    email = (settings.mercadopago_test_payer_email or "").strip()
    if not email:
        raise HTTPException(
            status_code=503,
            detail="Falta configurar el comprador de prueba de Mercado Pago.",
        )
    return email


def _autorizar(db: Session, cuenta_id: int, usuario: Usuario, *, escritura: bool) -> None:
    if obtener_cuenta(db, cuenta_id) is None:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada.")
    if usuario.rol == "administrador":
        return
    membresia = obtener_membresia(db, cuenta_id, usuario.id)
    if membresia is None:
        raise HTTPException(status_code=403, detail="No pertenece a la cuenta indicada.")
    if escritura and membresia.rol_cuenta not in {"propietario", "administrador"}:
        raise HTTPException(status_code=403, detail="Permisos insuficientes para administrar la suscripción.")


def _respuesta(suscripcion: Suscripcion) -> SuscripcionRespuesta:
    return SuscripcionRespuesta(
        cuenta_id=suscripcion.cuenta_id,
        plan=suscripcion.plan_code,
        estado=estado_efectivo(suscripcion),
        trial_started_at=suscripcion.trial_started_at,
        trial_ends_at=suscripcion.trial_ends_at,
        billing_provider=suscripcion.billing_provider,
        provider_status=suscripcion.mp_status,
        next_payment_at=suscripcion.next_payment_at,
        cancelled_at=suscripcion.cancelled_at,
    )


def _fecha(valor: Any) -> datetime | None:
    if not isinstance(valor, str) or not valor:
        return None
    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except ValueError:
        return None


def _evento(db: Session, suscripcion: Suscripcion, accion: str, anterior: str, nuevo: str, actor: Usuario | None = None) -> None:
    if anterior == nuevo:
        return
    db.add(EventoSuscripcion(
        cuenta_id=suscripcion.cuenta_id, suscripcion_id=suscripcion.id,
        actor_usuario_id=actor.id if actor else None,
        actor_tipo="usuario" if actor else "sistema", accion=accion,
        estado_anterior=anterior, estado_nuevo=nuevo,
        plan_anterior=suscripcion.plan_code, plan_nuevo=suscripcion.plan_code,
    ))


def _estado_preapproval(suscripcion: Suscripcion, remoto: dict[str, Any]) -> str:
    status = str(remoto.get("status") or "").lower()
    if status == "pending":
        return "trial" if estado_efectivo(suscripcion) == "trial" else "expired"
    if status == "authorized":
        # Autorizar débitos no prueba que una cuota haya sido cobrada.
        return "trial" if estado_efectivo(suscripcion) == "trial" else suscripcion.status
    if status == "paused":
        return "past_due"
    if status in {"canceled", "cancelled"}:
        return "cancelled"
    return suscripcion.status


def _aplicar_preapproval(db: Session, suscripcion: Suscripcion, remoto: dict[str, Any], *, actor: Usuario | None = None) -> bool:
    referencia = remoto.get("external_reference")
    plan_id = remoto.get("preapproval_plan_id")
    if referencia and suscripcion.external_reference and referencia != suscripcion.external_reference:
        raise HTTPException(status_code=409, detail="La referencia externa de la suscripción no coincide.")
    if plan_id and suscripcion.mp_preapproval_plan_id and plan_id != suscripcion.mp_preapproval_plan_id:
        raise HTTPException(status_code=409, detail="El plan externo de la suscripción no coincide.")
    version = remoto.get("version")
    modificado = _fecha(remoto.get("last_modified") or remoto.get("date_modified"))
    if isinstance(version, int) and suscripcion.mp_version is not None and version < suscripcion.mp_version:
        return False
    if modificado and suscripcion.mp_last_modified_at and desde_base_utc(modificado) < desde_base_utc(suscripcion.mp_last_modified_at):
        return False
    anterior = estado_efectivo(suscripcion)
    nuevo = _estado_preapproval(suscripcion, remoto)
    suscripcion.mp_status = str(remoto.get("status")) if remoto.get("status") is not None else suscripcion.mp_status
    suscripcion.mp_version = version if isinstance(version, int) else suscripcion.mp_version
    suscripcion.mp_last_modified_at = modificado or suscripcion.mp_last_modified_at
    suscripcion.mp_last_synced_at = ahora_utc()
    suscripcion.next_payment_at = _fecha(remoto.get("next_payment_date")) or suscripcion.next_payment_at
    if nuevo != anterior:
        suscripcion.status = nuevo
        if nuevo == "cancelled":
            suscripcion.cancelled_at = ahora_utc()
        _evento(db, suscripcion, "sincronizar_mercadopago", anterior, nuevo, actor)
    return True


def obtener_estado_suscripcion(db: Session, cuenta_id: int, usuario: Usuario) -> SuscripcionRespuesta:
    _autorizar(db, cuenta_id, usuario, escritura=False)
    suscripcion = obtener_suscripcion(db, cuenta_id)
    if suscripcion is None:
        raise HTTPException(status_code=404, detail="La cuenta no tiene una suscripción asociada.")
    return _respuesta(suscripcion)


def iniciar_suscripcion(
    db: Session,
    cuenta_id: int,
    usuario: Usuario,
    plan_code: str,
    card_token_id: str,
) -> IniciarSuscripcionRespuesta:
    _autorizar(db, cuenta_id, usuario, escritura=True)
    payer_email = _payer_email(usuario)
    suscripcion = obtener_suscripcion(db, cuenta_id, bloquear=True)
    if suscripcion is None:
        raise HTTPException(status_code=404, detail="La cuenta no tiene una suscripción asociada.")
    if suscripcion.mp_preapproval_id:
        raise HTTPException(status_code=409, detail="La cuenta ya tiene una suscripción de Mercado Pago.")
    plan = obtener_plan(db, plan_code, settings.mercadopago_env)
    precio = PRECIOS_PLANES[plan_code]
    if plan is None or plan.amount != precio or plan.currency != MONEDA:
        raise HTTPException(status_code=503, detail="El plan solicitado no está aprovisionado correctamente.")
    if suscripcion.trial_ends_at is None:
        raise HTTPException(status_code=409, detail="La suscripción no tiene una fecha de finalización del trial.")
    es_reintento = suscripcion.mp_idempotency_key is not None
    if es_reintento:
        if (
            suscripcion.plan_code != plan_code
            or suscripcion.mp_preapproval_plan_id != plan.mp_preapproval_plan_id
        ):
            raise HTTPException(
                status_code=409,
                detail="Ya existe un intento pendiente para otro plan.",
            )
    else:
        suscripcion.mp_idempotency_key = str(uuid4())
        suscripcion.external_reference = suscripcion.external_reference or str(uuid4())
        suscripcion.plan_code = plan_code
        suscripcion.billing_provider = "mercadopago"
        suscripcion.mp_preapproval_plan_id = plan.mp_preapproval_plan_id
        suscripcion.billing_amount = precio
        suscripcion.billing_currency = MONEDA
        try:
            # El intento se confirma antes de llamar al proveedor para que un
            # timeout o rollback posterior no genere una operación distinta.
            db.commit()
        except IntegrityError as error:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="No fue posible reservar el intento de suscripción.",
            ) from error
        suscripcion = obtener_suscripcion(db, cuenta_id, bloquear=True)
        if suscripcion is None:
            raise HTTPException(status_code=404, detail="La cuenta no tiene una suscripción asociada.")

    referencia = suscripcion.external_reference
    idempotency_key = suscripcion.mp_idempotency_key
    if referencia is None or idempotency_key is None:
        raise HTTPException(status_code=409, detail="El intento de suscripción está incompleto.")
    auto_recurring = {
        "frequency": 1,
        "frequency_type": "months",
        "transaction_amount": float(precio),
        "currency_id": MONEDA,
    }
    payload = {
        "preapproval_plan_id": plan.mp_preapproval_plan_id,
        "reason": f"Turnelia - Plan {plan_code}",
        "external_reference": referencia,
        "payer_email": payer_email,
        "card_token_id": card_token_id,
        "back_url": f"{settings.frontend_url}/suscripcion/retorno",
        "status": "authorized",
        "auto_recurring": auto_recurring,
    }
    try:
        gateway = _gateway()
        remoto = None
        if es_reintento:
            coincidencias = [
                item
                for item in gateway.buscar_preapprovals(referencia)
                if item.get("external_reference") == referencia
                and item.get("preapproval_plan_id")
                == suscripcion.mp_preapproval_plan_id
                and item.get("payer_email") == payer_email
            ]
            if len(coincidencias) > 1:
                raise HTTPException(
                    status_code=409,
                    detail="Mercado Pago devolvió más de una suscripción para el intento pendiente.",
                )
            if coincidencias:
                remoto = coincidencias[0]
        if remoto is None:
            remoto = gateway.crear_preapproval(
                payload,
                idempotency_key=idempotency_key,
            )
    except MercadoPagoSubscriptionError as error:
        _registrar_error_proveedor(error)
        db.rollback()
        raise HTTPException(status_code=502, detail="No fue posible iniciar la suscripción.") from error
    preapproval_id = remoto.get("id")
    checkout_url = remoto.get("init_point") or remoto.get("sandbox_init_point")
    if not isinstance(preapproval_id, str):
        db.rollback()
        raise HTTPException(status_code=502, detail="Mercado Pago devolvió una respuesta incompleta.")
    if not isinstance(checkout_url, str):
        checkout_url = None
    suscripcion.mp_preapproval_id = preapproval_id
    suscripcion.mp_idempotency_key = None
    _aplicar_preapproval(db, suscripcion, remoto, actor=usuario)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="La suscripción ya fue iniciada.") from error
    return IniciarSuscripcionRespuesta(estado=estado_efectivo(suscripcion), checkout_url=checkout_url)


def sincronizar_suscripcion(db: Session, cuenta_id: int, usuario: Usuario) -> OperacionSuscripcionRespuesta:
    _autorizar(db, cuenta_id, usuario, escritura=True)
    suscripcion = obtener_suscripcion(db, cuenta_id, bloquear=True)
    if suscripcion is None or not suscripcion.mp_preapproval_id:
        raise HTTPException(status_code=409, detail="La cuenta no tiene una suscripción de Mercado Pago.")
    try:
        remoto = _gateway().consultar_preapproval(suscripcion.mp_preapproval_id)
    except MercadoPagoSubscriptionError as error:
        _registrar_error_proveedor(error)
        db.rollback()
        raise HTTPException(status_code=502, detail="No fue posible sincronizar la suscripción.") from error
    procesado = _aplicar_preapproval(db, suscripcion, remoto, actor=usuario)
    db.commit()
    return OperacionSuscripcionRespuesta(procesado=procesado, suscripcion=_respuesta(suscripcion))


def cancelar_suscripcion(db: Session, cuenta_id: int, usuario: Usuario) -> OperacionSuscripcionRespuesta:
    _autorizar(db, cuenta_id, usuario, escritura=True)
    suscripcion = obtener_suscripcion(db, cuenta_id, bloquear=True)
    if suscripcion is None or not suscripcion.mp_preapproval_id:
        raise HTTPException(status_code=409, detail="La cuenta no tiene una suscripción de Mercado Pago.")
    if suscripcion.status == "cancelled" or suscripcion.mp_status in {"canceled", "cancelled"}:
        return OperacionSuscripcionRespuesta(procesado=False, suscripcion=_respuesta(suscripcion))
    try:
        remoto = _gateway().cancelar_preapproval(suscripcion.mp_preapproval_id)
    except MercadoPagoSubscriptionError as error:
        _registrar_error_proveedor(error)
        db.rollback()
        raise HTTPException(status_code=502, detail="No fue posible cancelar la suscripción.") from error
    procesado = _aplicar_preapproval(db, suscripcion, remoto, actor=usuario)
    db.commit()
    return OperacionSuscripcionRespuesta(procesado=procesado, suscripcion=_respuesta(suscripcion))


def _aplicar_cobro(db: Session, suscripcion: Suscripcion, remoto: dict[str, Any], resource_id: str, *, es_payment: bool = False) -> bool:
    status = str(remoto.get("status") or "").lower()
    existente = obtener_cobro_por_payment(db, resource_id) if es_payment else obtener_cobro(db, resource_id)
    actualizado = _fecha(remoto.get("date_modified") or remoto.get("last_modified"))
    if existente and existente.provider_updated_at and actualizado and desde_base_utc(actualizado) < desde_base_utc(existente.provider_updated_at):
        return False
    monto = Decimal(str(remoto.get("transaction_amount") or remoto.get("amount") or 0))
    moneda = str(remoto.get("currency_id") or remoto.get("currency") or "")
    if suscripcion.billing_amount is None or monto != suscripcion.billing_amount or moneda != suscripcion.billing_currency:
        raise HTTPException(status_code=409, detail="El monto o la moneda del cobro no coincide con la suscripción.")
    cobro = existente or CobroSuscripcion(
        suscripcion_id=suscripcion.id,
        mp_authorized_payment_id=None if es_payment else resource_id,
        mp_payment_id=resource_id if es_payment else None,
        amount=monto,
        currency=moneda,
        status=status or "unknown",
    )
    cobro.status = status or cobro.status
    cobro.status_detail = remoto.get("status_detail")
    cobro.provider_updated_at = actualizado
    if existente is None:
        db.add(cobro)
    anterior = estado_efectivo(suscripcion)
    nuevo = anterior
    if status == "approved":
        nuevo = "active"
        suscripcion.billing_started_at = suscripcion.billing_started_at or ahora_utc()
    elif status in {"rejected", "refunded", "charged_back"}:
        nuevo = "past_due"
    if nuevo != anterior:
        suscripcion.status = nuevo
        _evento(db, suscripcion, "cobro_mercadopago", anterior, nuevo)
    return True


def procesar_webhook_suscripcion(db: Session, *, topic: str, resource_id: str, request_id: str | None, action: str | None, payload: dict[str, Any]) -> bool:
    payload_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    event_key = f"{topic}:{resource_id}:{action or ''}:{request_id or payload_hash}"
    if obtener_notificacion(db, event_key) is not None:
        return False
    notificacion = NotificacionMercadoPagoSuscripcion(
        event_key=event_key, topic=topic, action=action, resource_id=resource_id,
        request_id=request_id, payload_hash=payload_hash,
    )
    db.add(notificacion)
    try:
        gateway = _gateway()
        if topic == "subscription_preapproval":
            remoto = gateway.consultar_preapproval(resource_id)
            suscripcion = obtener_suscripcion_por_preapproval(db, str(remoto.get("id") or resource_id), bloquear=True)
            if suscripcion is None:
                notificacion.processing_status = "ignored"
                db.commit()
                return False
            procesado = _aplicar_preapproval(db, suscripcion, remoto)
        elif topic in {"subscription_authorized_payment", "payment"}:
            remoto = gateway.consultar_payment(resource_id) if topic == "payment" else gateway.consultar_authorized_payment(resource_id)
            preapproval_id = remoto.get("preapproval_id") or remoto.get("subscription_id") or (remoto.get("metadata") or {}).get("preapproval_id")
            suscripcion = obtener_suscripcion_por_preapproval(db, str(preapproval_id), bloquear=True) if preapproval_id else None
            if suscripcion is None:
                notificacion.processing_status = "ignored"
                db.commit()
                return False
            procesado = _aplicar_cobro(db, suscripcion, remoto, resource_id, es_payment=topic == "payment")
        else:  # Los cambios de catálogo no alteran suscripciones contratadas.
            gateway.consultar_plan(resource_id)
            procesado = False
        notificacion.processing_status = "processed" if procesado else "ignored"
        notificacion.processed_at = ahora_utc()
        db.commit()
        return procesado
    except MercadoPagoSubscriptionError as error:
        _registrar_error_proveedor(error)
        db.rollback()
        raise HTTPException(status_code=502, detail="No fue posible verificar la notificación.") from error
    except IntegrityError:
        db.rollback()
        return False
