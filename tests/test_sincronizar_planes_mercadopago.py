from decimal import Decimal

from app.scripts.sincronizar_planes_mercadopago import (
    payload_plan,
    plan_remoto_coincide,
)


def test_payload_plan_declara_trial_gratuito_de_14_dias():
    payload = payload_plan("profesional", Decimal("34900.00"))

    assert payload["auto_recurring"] == {
        "frequency": 1,
        "frequency_type": "months",
        "free_trial": {"frequency": 14, "frequency_type": "days"},
        "transaction_amount": 34900.0,
        "currency_id": "ARS",
    }


def test_plan_remoto_invalido_no_se_considera_sincronizado():
    remoto = {
        "auto_recurring": {
            "frequency": 1,
            "frequency_type": "months",
            "transaction_amount": 34900.0,
            "currency_id": "ARS",
        }
    }

    assert plan_remoto_coincide(remoto, Decimal("34900.00")) is False


def test_plan_remoto_valido_coincide_con_catalogo():
    remoto = {
        "auto_recurring": {
            "frequency": 1,
            "frequency_type": "months",
            "free_trial": {"frequency": 14, "frequency_type": "days"},
            "transaction_amount": 34900.0,
            "currency_id": "ARS",
        }
    }

    assert plan_remoto_coincide(remoto, Decimal("34900.00")) is True