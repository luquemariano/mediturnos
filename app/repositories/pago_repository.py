from datetime import datetime
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


def bloquear_turno_para_pago(
    db: Session,
    turno_id: int,
) -> Turno | None:
    consulta = db.query(Turno).filter(Turno.id == turno_id)

    if db.get_bind().dialect.name == "postgresql":
        consulta = consulta.with_for_update()

    return consulta.execution_options(
        populate_existing=True,
    ).first()


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


def buscar_pago_por_id_para_actualizar(
    db: Session,
    pago_id: int,
) -> Pago | None:
    consulta = db.query(Pago).filter(Pago.id == pago_id)

    if db.get_bind().dialect.name == "postgresql":
        consulta = consulta.with_for_update()

    return consulta.execution_options(
        populate_existing=True,
    ).first()


def buscar_pago_por_payment_id(
    db: Session,
    payment_id: str,
) -> Pago | None:
    return (
        db.query(Pago)
        .filter(Pago.payment_id == payment_id)
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
    db.flush()

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
    mp_actualizado_en: datetime | None,
) -> Pago:
    pago.payment_id = payment_id
    pago.estado = estado
    pago.mp_actualizado_en = mp_actualizado_en

    return pago
