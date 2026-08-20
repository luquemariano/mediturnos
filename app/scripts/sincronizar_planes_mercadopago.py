"""Aprovisiona una sola vez los planes SaaS de Mercado Pago por ambiente."""

import argparse
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import SessionLocal
from app.models.mercadopago_plan_suscripcion import MercadoPagoPlanSuscripcion
from app.repositories.suscripcion_repository import obtener_plan
from app.services.mercadopago_subscription_service import MercadoPagoSubscriptionService
from app.services.cuenta_service import TRIAL_DIAS
from app.services.suscripcion_mercadopago_service import MONEDA, PRECIOS_PLANES


def payload_plan(plan_code: str, importe: Decimal) -> dict[str, object]:
    return {
        "reason": f"Turnelia - Plan {plan_code}",
        "auto_recurring": {
            "frequency": 1,
            "frequency_type": "months",
            "free_trial": {
                "frequency": TRIAL_DIAS,
                "frequency_type": "days",
            },
            "transaction_amount": float(importe),
            "currency_id": MONEDA,
        },
        "back_url": f"{settings.frontend_url}/suscripcion/retorno",
    }


def plan_remoto_coincide(remoto: dict[str, object], importe: Decimal) -> bool:
    recurrencia = remoto.get("auto_recurring")
    if not isinstance(recurrencia, dict):
        return False
    prueba = recurrencia.get("free_trial")
    return (
        recurrencia.get("frequency") == 1
        and recurrencia.get("frequency_type") == "months"
        and recurrencia.get("transaction_amount") == float(importe)
        and recurrencia.get("currency_id") == MONEDA
        and isinstance(prueba, dict)
        and prueba.get("frequency") == TRIAL_DIAS
        and prueba.get("frequency_type") == "days"
    )


def sincronizar_planes(
    db: Session,
    gateway: MercadoPagoSubscriptionService,
    plan_codes: list[str] | None = None,
) -> list[MercadoPagoPlanSuscripcion]:
    resultado = []
    seleccion = plan_codes or list(PRECIOS_PLANES)
    for plan_code in seleccion:
        importe = PRECIOS_PLANES[plan_code]
        existente = obtener_plan(db, plan_code, settings.mercadopago_env)
        if existente is not None:
            remoto = gateway.consultar_plan(existente.mp_preapproval_plan_id)
            if not plan_remoto_coincide(remoto, importe):
                raise RuntimeError(
                    f"El plan remoto {plan_code} no coincide con el catálogo SaaS "
                    "incluido el trial gratuito de 14 días; actualizalo o reemplazalo "
                    "antes de sincronizarlo."
                )
            resultado.append(existente)
            continue
        remoto = gateway.crear_plan(payload_plan(plan_code, importe))
        plan_id = remoto.get("id")
        if not isinstance(plan_id, str) or not plan_id:
            raise RuntimeError("Mercado Pago devolvió un plan sin identificador.")
        modelo = MercadoPagoPlanSuscripcion(
            plan_code=plan_code, environment=settings.mercadopago_env,
            mp_preapproval_plan_id=plan_id, amount=Decimal(importe), currency=MONEDA,
        )
        db.add(modelo)
        db.flush()
        resultado.append(modelo)
    db.commit()
    return resultado


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--plan",
        action="append",
        choices=tuple(PRECIOS_PLANES),
        dest="planes",
        help="Limita la sincronización al plan indicado.",
    )
    argumentos = parser.parse_args()
    token = settings.mercadopago_access_token
    if token is None or not token.get_secret_value().strip():
        raise RuntimeError("MERCADOPAGO_ACCESS_TOKEN es obligatorio.")
    db = SessionLocal()
    gateway = MercadoPagoSubscriptionService(token.get_secret_value())
    try:
        planes = sincronizar_planes(db, gateway, argumentos.planes)
        print(f"Planes de Mercado Pago sincronizados: {len(planes)}")
    except Exception:
        db.rollback()
        raise
    finally:
        gateway.close()
        db.close()


if __name__ == "__main__":
    main()
