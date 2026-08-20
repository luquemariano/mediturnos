from sqlalchemy.orm import Session

from app.models.cobro_suscripcion import CobroSuscripcion
from app.models.cuenta import Cuenta
from app.models.cuenta_usuario import CuentaUsuario
from app.models.mercadopago_plan_suscripcion import MercadoPagoPlanSuscripcion
from app.models.notificacion_mercadopago_suscripcion import (
    NotificacionMercadoPagoSuscripcion,
)
from app.models.suscripcion import Suscripcion


def obtener_membresia(db: Session, cuenta_id: int, usuario_id: int) -> CuentaUsuario | None:
    return db.get(CuentaUsuario, (cuenta_id, usuario_id))


def obtener_cuenta(db: Session, cuenta_id: int) -> Cuenta | None:
    return db.get(Cuenta, cuenta_id)


def obtener_suscripcion(db: Session, cuenta_id: int, *, bloquear: bool = False) -> Suscripcion | None:
    consulta = db.query(Suscripcion).filter(Suscripcion.cuenta_id == cuenta_id)
    if bloquear:
        consulta = consulta.with_for_update()
    return consulta.one_or_none()


def obtener_suscripcion_por_preapproval(db: Session, preapproval_id: str, *, bloquear: bool = False) -> Suscripcion | None:
    consulta = db.query(Suscripcion).filter(Suscripcion.mp_preapproval_id == preapproval_id)
    if bloquear:
        consulta = consulta.with_for_update()
    return consulta.one_or_none()


def obtener_plan(db: Session, plan_code: str, environment: str) -> MercadoPagoPlanSuscripcion | None:
    return (
        db.query(MercadoPagoPlanSuscripcion)
        .filter(
            MercadoPagoPlanSuscripcion.plan_code == plan_code,
            MercadoPagoPlanSuscripcion.environment == environment,
            MercadoPagoPlanSuscripcion.active.is_(True),
        )
        .one_or_none()
    )


def obtener_notificacion(db: Session, event_key: str) -> NotificacionMercadoPagoSuscripcion | None:
    return (
        db.query(NotificacionMercadoPagoSuscripcion)
        .filter(NotificacionMercadoPagoSuscripcion.event_key == event_key)
        .one_or_none()
    )


def obtener_cobro(db: Session, authorized_payment_id: str) -> CobroSuscripcion | None:
    return (
        db.query(CobroSuscripcion)
        .filter(CobroSuscripcion.mp_authorized_payment_id == authorized_payment_id)
        .one_or_none()
    )


def obtener_cobro_por_payment(db: Session, payment_id: str) -> CobroSuscripcion | None:
    return (
        db.query(CobroSuscripcion)
        .filter(CobroSuscripcion.mp_payment_id == payment_id)
        .one_or_none()
    )
