from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.models.cuenta import Cuenta
from app.models.mercadopago_plan_suscripcion import MercadoPagoPlanSuscripcion
from app.models.suscripcion import Suscripcion
from tests.conftest import SessionTest


def test_suscripcion_legacy_usa_billing_manual_y_campos_externos_nulos():
    with SessionTest() as db:
        cuenta = Cuenta(nombre="Cuenta legacy", tipo="individual")
        suscripcion = Suscripcion(cuenta=cuenta, plan_code="profesional", status="active")
        db.add(suscripcion)
        db.commit()
        db.refresh(suscripcion)

        assert suscripcion.billing_provider == "manual"
        assert suscripcion.external_reference is None
        assert suscripcion.mp_preapproval_id is None
        assert suscripcion.mp_preapproval_plan_id is None
        assert suscripcion.mp_idempotency_key is None
        assert suscripcion.billing_amount is None


def test_catalogo_impide_duplicar_plan_por_ambiente():
    with SessionTest() as db:
        db.add_all(
            [
                MercadoPagoPlanSuscripcion(
                    plan_code="profesional",
                    environment="sandbox",
                    mp_preapproval_plan_id="plan-1",
                    amount=Decimal("34900.00"),
                    currency="ARS",
                ),
                MercadoPagoPlanSuscripcion(
                    plan_code="profesional",
                    environment="sandbox",
                    mp_preapproval_plan_id="plan-2",
                    amount=Decimal("34900.00"),
                    currency="ARS",
                ),
            ]
        )

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
        else:
            raise AssertionError("Se permitió duplicar un plan en el mismo ambiente")
