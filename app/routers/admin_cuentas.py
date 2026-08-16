from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import requiere_administrador
from app.database.connection import obtener_db
from app.models.usuario import Usuario
from app.schemas.admin_cuenta import (
    AdminCuentaDetalleRespuesta,
    AdminCuentasPaginaRespuesta,
    AdminCuentasResumenRespuesta,
    AdminAccionMotivoEntrada, AdminExtenderTrialEntrada, AdminCambiarPlanEntrada,
    AdminEventoSuscripcionRespuesta,
)
from app.services.admin_cuenta_service import (
    obtener_cuentas_admin,
    obtener_detalle_cuenta_admin,
    obtener_resumen_admin,
    activar_suscripcion_admin, reactivar_suscripcion_admin,
    marcar_pago_pendiente_admin, cancelar_suscripcion_admin,
    extender_trial_admin, cambiar_plan_admin, obtener_historial_admin,
)


EstadoFiltro = Literal["trial", "active", "past_due", "cancelled", "expired"]
PlanFiltro = Literal["profesional", "consultorio", "centro"]

router = APIRouter(prefix="/admin/cuentas", tags=["Administración comercial"])


@router.get("", response_model=AdminCuentasPaginaRespuesta)
def listar_cuentas(
    q: str | None = Query(default=None, max_length=100),
    estado: EstadoFiltro | None = None,
    plan: PlanFiltro | None = None,
    created_from: date | None = None,
    created_to: date | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(obtener_db),
    _: Usuario = Depends(requiere_administrador),
):
    return obtener_cuentas_admin(
        db, q=q, estado=estado, plan=plan,
        created_from=created_from, created_to=created_to,
        offset=offset, limit=limit,
    )


@router.get("/resumen", response_model=AdminCuentasResumenRespuesta)
def resumen_cuentas(
    db: Session = Depends(obtener_db),
    _: Usuario = Depends(requiere_administrador),
):
    return obtener_resumen_admin(db)


@router.get("/{cuenta_id}", response_model=AdminCuentaDetalleRespuesta)
def detalle_cuenta(
    cuenta_id: int,
    db: Session = Depends(obtener_db),
    _: Usuario = Depends(requiere_administrador),
):
    return obtener_detalle_cuenta_admin(db, cuenta_id)


@router.post("/{cuenta_id}/suscripcion/activar", response_model=AdminCuentaDetalleRespuesta)
def activar(cuenta_id: int, entrada: AdminAccionMotivoEntrada, db: Session = Depends(obtener_db), actor: Usuario = Depends(requiere_administrador)):
    return activar_suscripcion_admin(db, cuenta_id, actor, entrada.motivo)


@router.post("/{cuenta_id}/suscripcion/reactivar", response_model=AdminCuentaDetalleRespuesta)
def reactivar(cuenta_id: int, entrada: AdminAccionMotivoEntrada, db: Session = Depends(obtener_db), actor: Usuario = Depends(requiere_administrador)):
    return reactivar_suscripcion_admin(db, cuenta_id, actor, entrada.motivo)


@router.post("/{cuenta_id}/suscripcion/marcar-pago-pendiente", response_model=AdminCuentaDetalleRespuesta)
def marcar_pago_pendiente(cuenta_id: int, entrada: AdminAccionMotivoEntrada, db: Session = Depends(obtener_db), actor: Usuario = Depends(requiere_administrador)):
    return marcar_pago_pendiente_admin(db, cuenta_id, actor, entrada.motivo)


@router.post("/{cuenta_id}/suscripcion/cancelar", response_model=AdminCuentaDetalleRespuesta)
def cancelar(cuenta_id: int, entrada: AdminAccionMotivoEntrada, db: Session = Depends(obtener_db), actor: Usuario = Depends(requiere_administrador)):
    return cancelar_suscripcion_admin(db, cuenta_id, actor, entrada.motivo)


@router.post("/{cuenta_id}/suscripcion/extender-trial", response_model=AdminCuentaDetalleRespuesta)
def extender_trial(cuenta_id: int, entrada: AdminExtenderTrialEntrada, db: Session = Depends(obtener_db), actor: Usuario = Depends(requiere_administrador)):
    return extender_trial_admin(db, cuenta_id, actor, entrada.dias, entrada.motivo)


@router.post("/{cuenta_id}/suscripcion/cambiar-plan", response_model=AdminCuentaDetalleRespuesta)
def cambiar_plan(cuenta_id: int, entrada: AdminCambiarPlanEntrada, db: Session = Depends(obtener_db), actor: Usuario = Depends(requiere_administrador)):
    return cambiar_plan_admin(db, cuenta_id, actor, entrada.plan, entrada.motivo)


@router.get("/{cuenta_id}/suscripcion/historial", response_model=list[AdminEventoSuscripcionRespuesta])
def historial(cuenta_id: int, db: Session = Depends(obtener_db), _: Usuario = Depends(requiere_administrador)):
    return obtener_historial_admin(db, cuenta_id)
