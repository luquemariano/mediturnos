from datetime import datetime
from decimal import Decimal, InvalidOperation

import mercadopago
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.datetime_utils import desde_base_utc
from app.models.pago import Pago
from app.models.turno import Turno
from app.models.usuario import Usuario
from app.repositories.pago_repository import (
    actualizar_pago_desde_mercado_pago,
    bloquear_turno_para_pago,
    buscar_pago_por_id_para_actualizar,
    buscar_pago_por_payment_id,
    buscar_pago_por_turno,
    buscar_turno_por_id,
    crear_pago_pendiente,
    guardar_datos_preferencia,
)
from app.repositories.turno_repository import (
    bloquear_agenda_profesional,
)
from app.services.turno_service import (
    ESTADOS_TERMINALES,
    aplicar_transicion_estado,
    es_conflicto_agenda,
)


ESTADOS_PAGO_NEGATIVOS = {
    "rejected",
    "cancelled",
    "refunded",
    "charged_back",
}
MOTIVO_HORARIO_REUTILIZADO = "horario_reutilizado"


def validar_acceso_pago(
    db: Session,
    turno_id: int,
    usuario_actual: Usuario,
) -> Turno:
    turno = buscar_turno_por_id(db, turno_id)

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
    validar_acceso_pago(db, turno_id, usuario_actual)
    turno = bloquear_turno_para_pago(db, turno_id)

    if turno is None:
        raise HTTPException(
            status_code=404,
            detail="Turno no encontrado.",
        )

    if turno.estado in {"cancelado", "finalizado"}:
        raise HTTPException(
            status_code=400,
            detail="El turno no admite pagos.",
        )

    pago = buscar_pago_por_turno(db, turno_id)

    if pago is not None:
        if pago.estado == "approved":
            raise HTTPException(
                status_code=409,
                detail="El turno ya se encuentra pagado.",
            )

        if (
            pago.preference_id is not None
            and pago.init_point is not None
        ):
            return pago

    access_token = settings.mercado_pago_access_token

    if not access_token:
        raise HTTPException(
            status_code=500,
            detail="Mercado Pago no está configurado.",
        )

    monto = Decimal(str(turno.prestacion.precio))

    if pago is None:
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
        "metadata": {
            "pago_id": pago.id,
            "turno_id": turno.id,
        },
    }
    respuesta = sdk.preference().create(preference_data)

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

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise

    db.refresh(pago)
    return pago


def _fecha_actualizacion_mp(datos_pago: dict) -> datetime | None:
    valor = datos_pago.get("date_last_updated")

    if not valor:
        return None

    try:
        fecha = datetime.fromisoformat(
            str(valor).replace("Z", "+00:00")
        )
    except ValueError as error:
        raise HTTPException(
            status_code=502,
            detail="Mercado Pago devolvió una fecha inválida.",
        ) from error

    if fecha.tzinfo is None:
        raise HTTPException(
            status_code=502,
            detail="Mercado Pago devolvió una fecha sin zona horaria.",
        )

    return fecha


def _preference_id_desde_mercado_pago(
    sdk,
    datos_pago: dict,
) -> str | None:
    preference_id = datos_pago.get("preference_id")

    if preference_id:
        return str(preference_id)

    order_id = (datos_pago.get("order") or {}).get("id")

    if order_id is None:
        return None

    respuesta = sdk.merchant_order().get(order_id)

    if respuesta["status"] != 200:
        raise HTTPException(
            status_code=502,
            detail=(
                "No se pudo validar la preferencia en "
                "Mercado Pago."
            ),
        )

    preference_id = respuesta["response"].get("preference_id")
    return str(preference_id) if preference_id else None


def _resolver_pago_local(
    db: Session,
    datos_pago: dict,
    payment_id: str,
) -> Pago | None:
    metadata = datos_pago.get("metadata") or {}
    pago_id = metadata.get("pago_id")

    if pago_id is not None:
        try:
            pago_id = int(pago_id)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=409,
                detail="La referencia interna del pago es inválida.",
            ) from None

        return buscar_pago_por_id_para_actualizar(db, pago_id)

    pago = buscar_pago_por_payment_id(db, payment_id)

    if pago is not None:
        return buscar_pago_por_id_para_actualizar(db, pago.id)

    external_reference = datos_pago.get("external_reference")

    try:
        turno_id = int(external_reference)
    except (TypeError, ValueError):
        return None

    pago = buscar_pago_por_turno(db, turno_id)

    if pago is not None:
        return buscar_pago_por_id_para_actualizar(db, pago.id)

    return None


def _validar_pago_mercado_pago(
    pago: Pago,
    datos_pago: dict,
    payment_id: str,
    preference_id: str | None,
) -> None:
    if str(datos_pago.get("id")) != payment_id:
        raise HTTPException(
            status_code=409,
            detail="El identificador del pago no coincide.",
        )

    if str(datos_pago.get("external_reference")) != str(
        pago.turno_id
    ):
        raise HTTPException(
            status_code=409,
            detail="La referencia del turno no coincide.",
        )

    metadata = datos_pago.get("metadata") or {}
    turno_metadata = metadata.get("turno_id")

    if (
        turno_metadata is not None
        and str(turno_metadata) != str(pago.turno_id)
    ):
        raise HTTPException(
            status_code=409,
            detail="La referencia interna del turno no coincide.",
        )

    if (
        pago.preference_id is not None
        and preference_id != pago.preference_id
    ):
        raise HTTPException(
            status_code=409,
            detail="La preferencia del pago no coincide.",
        )

    try:
        monto = Decimal(str(datos_pago["transaction_amount"]))
    except (KeyError, InvalidOperation):
        raise HTTPException(
            status_code=409,
            detail="El monto del pago no es válido.",
        ) from None

    if monto != pago.monto:
        raise HTTPException(
            status_code=409,
            detail="El monto del pago no coincide.",
        )

    if datos_pago.get("currency_id") != "ARS":
        raise HTTPException(
            status_code=409,
            detail="La moneda del pago no coincide.",
        )


def _evento_es_anterior(
    pago: Pago,
    mp_actualizado_en: datetime | None,
) -> bool:
    if (
        pago.mp_actualizado_en is None
        or mp_actualizado_en is None
    ):
        return False

    return mp_actualizado_en < desde_base_utc(
        pago.mp_actualizado_en
    )


def _misma_fecha_mp(
    pago: Pago,
    mp_actualizado_en: datetime | None,
) -> bool:
    if pago.mp_actualizado_en is None:
        return mp_actualizado_en is None

    if mp_actualizado_en is None:
        return False

    return desde_base_utc(
        pago.mp_actualizado_en
    ) == mp_actualizado_en


def _persistir_revision_horario(
    db: Session,
    pago_id: int,
    payment_id: str,
    mp_actualizado_en: datetime | None,
) -> Pago:
    pago = buscar_pago_por_id_para_actualizar(db, pago_id)

    if pago is None:
        raise HTTPException(
            status_code=404,
            detail="Pago no encontrado.",
        )

    actualizar_pago_desde_mercado_pago(
        pago,
        payment_id,
        "approved",
        mp_actualizado_en,
    )
    pago.requiere_revision = True
    pago.motivo_revision = MOTIVO_HORARIO_REUTILIZADO

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

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
    respuesta = sdk.payment().get(payment_id)

    if respuesta["status"] != 200:
        raise HTTPException(
            status_code=502,
            detail="No se pudo consultar el pago en Mercado Pago.",
        )

    datos_pago = respuesta["response"]
    pago = _resolver_pago_local(db, datos_pago, payment_id)

    if pago is None:
        return None

    preference_id = _preference_id_desde_mercado_pago(
        sdk,
        datos_pago,
    )
    _validar_pago_mercado_pago(
        pago,
        datos_pago,
        payment_id,
        preference_id,
    )
    estado = datos_pago["status"]
    mp_actualizado_en = _fecha_actualizacion_mp(datos_pago)
    mismo_intento = (
        pago.payment_id is None
        or pago.payment_id == payment_id
    )

    if not mismo_intento:
        reemplazo_aprobado = (
            pago.estado != "approved"
            and estado == "approved"
        )

        if not reemplazo_aprobado:
            return pago
    elif _evento_es_anterior(pago, mp_actualizado_en):
        return pago

    if (
        pago.payment_id == payment_id
        and pago.estado == estado
        and _misma_fecha_mp(pago, mp_actualizado_en)
    ):
        return pago

    turno = pago.turno
    estado_turno_inicial = turno.estado
    pago_id = pago.id

    if estado == "approved" and turno.estado == "cancelado":
        bloquear_agenda_profesional(db, turno.profesional_id)
        db.refresh(turno)
        estado_turno_inicial = turno.estado

    actualizar_pago_desde_mercado_pago(
        pago,
        payment_id,
        estado,
        mp_actualizado_en,
    )
    pago.requiere_revision = False
    pago.motivo_revision = None

    if estado == "approved":
        if turno.estado not in ESTADOS_TERMINALES:
            aplicar_transicion_estado(turno, "confirmado")
    elif (
        estado in ESTADOS_PAGO_NEGATIVOS
        and turno.estado not in ESTADOS_TERMINALES
    ):
        aplicar_transicion_estado(turno, "cancelado")

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()

        if (
            estado == "approved"
            and estado_turno_inicial == "cancelado"
            and es_conflicto_agenda(error)
        ):
            return _persistir_revision_horario(
                db,
                pago_id,
                payment_id,
                mp_actualizado_en,
            )

        raise

    db.refresh(pago)
    return pago


def obtener_pago_por_turno(
    db: Session,
    turno_id: int,
    usuario_actual: Usuario,
) -> Pago:
    validar_acceso_pago(db, turno_id, usuario_actual)
    pago = buscar_pago_por_turno(db, turno_id)

    if pago is None:
        raise HTTPException(
            status_code=404,
            detail="No se encontró un pago para el turno.",
        )

    return pago
