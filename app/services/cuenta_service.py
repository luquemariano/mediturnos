from datetime import datetime, timedelta
from math import ceil

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.datetime_utils import ahora_utc, desde_base_utc
from app.models.cuenta import Cuenta
from app.models.cuenta_usuario import CuentaUsuario
from app.models.suscripcion import Suscripcion
from app.models.usuario import Usuario
from app.repositories.cuenta_repository import listar_membresias_usuario
from app.schemas.cuenta import CuentaActualRespuesta


TRIAL_DIAS = 14


def crear_cuenta_individual_con_trial(nombre: str, usuario: Usuario, ahora: datetime | None = None) -> Cuenta:
    inicio = ahora or ahora_utc()
    cuenta = Cuenta(nombre=nombre, tipo="individual")
    cuenta.membresias.append(CuentaUsuario(usuario=usuario, rol_cuenta="propietario"))
    cuenta.suscripcion = Suscripcion(
        plan_code="profesional", status="trial",
        trial_started_at=inicio, trial_ends_at=inicio + timedelta(days=TRIAL_DIAS),
    )
    return cuenta


def estado_efectivo(suscripcion: Suscripcion, ahora: datetime | None = None) -> str:
    instante = ahora or ahora_utc()
    if suscripcion.status == "trial" and suscripcion.trial_ends_at is not None:
        if instante >= desde_base_utc(suscripcion.trial_ends_at):
            return "expired"
    return suscripcion.status


def dias_trial_restantes(suscripcion: Suscripcion, ahora: datetime | None = None) -> int:
    if suscripcion.trial_ends_at is None:
        return 0
    segundos = (desde_base_utc(suscripcion.trial_ends_at) - (ahora or ahora_utc())).total_seconds()
    return max(0, ceil(segundos / 86400))


def obtener_cuenta_actual(db: Session, usuario: Usuario) -> CuentaActualRespuesta:
    membresias = listar_membresias_usuario(db, usuario.id)
    if not membresias:
        raise HTTPException(status_code=404, detail="El usuario no tiene una cuenta asociada.")

    membresia = next(
        (item for item in membresias if usuario.profesional is not None and item.cuenta_id == usuario.profesional.cuenta_id),
        membresias[0] if len(membresias) == 1 else None,
    )
    if membresia is None:
        raise HTTPException(status_code=409, detail="El usuario pertenece a varias cuentas; debe seleccionar una cuenta actual.")
    suscripcion = membresia.cuenta.suscripcion
    if suscripcion is None:
        raise HTTPException(status_code=404, detail="La cuenta no tiene una suscripción asociada.")
    return CuentaActualRespuesta(
        cuenta_id=membresia.cuenta_id,
        plan=suscripcion.plan_code,
        subscription_status=estado_efectivo(suscripcion),
        trial_started_at=suscripcion.trial_started_at,
        trial_ends_at=suscripcion.trial_ends_at,
        trial_days_remaining=dias_trial_restantes(suscripcion),
    )
