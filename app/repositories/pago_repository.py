from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.pago import Pago
from app.models.turno import Turno


def buscar_turno_por_id(
    db: Session,
    turno_id: int,
) -> Turno | None:
    return (
        db.query(Turno)
        .filter(Turno.id == turno_id)
        .first()
    )


def buscar_pago_por_turno(
    db: Session,
    turno_id: int,
) -> Pago | None:
    return (
        db.query(Pago)
        .filter(Pago.turno_id == turno_id)
        .order_by(Pago.id.desc())
        .first()
    )


def crear_pago_pendiente(
    db: Session,
    turno_id: int,
    monto: Decimal,
) -> Pago:
    pago = Pago(
        turno_id=turno_id,
        monto=monto,
        estado="pendiente",
    )

    db.add(pago)

    return pago


def guardar_datos_preferencia(
    pago: Pago,
    preference_id: str,
    init_point: str,
) -> Pago:
    pago.preference_id = preference_id
    pago.init_point = init_point

    return pago

def buscar_pago_por_preferencia(
    db: Session,
    preference_id: str,
) -> Pago | None:
    return (
        db.query(Pago)
        .filter(Pago.preference_id == preference_id)
        .first()
    )


def actualizar_pago_desde_mercado_pago(
    pago: Pago,
    payment_id: str,
    estado: str,
) -> Pago:
    pago.payment_id = payment_id
    pago.estado = estado

    return pago