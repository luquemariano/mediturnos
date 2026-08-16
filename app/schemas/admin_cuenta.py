from datetime import datetime
from typing import Literal

from pydantic import BaseModel


PlanCode = Literal["profesional", "consultorio", "centro"]
EstadoSuscripcion = Literal[
    "trial", "active", "past_due", "cancelled", "expired",
]
EstadoCuentaAdmin = Literal[
    "trial", "active", "past_due", "cancelled", "expired",
    "sin_suscripcion",
]


class AdminProfesionalPrincipalRespuesta(BaseModel):
    profesional_id: int
    nombre: str
    apellido: str
    matricula: str
    email: str | None


class AdminCuentaItemRespuesta(BaseModel):
    cuenta_id: int
    nombre: str
    tipo: Literal["individual", "organizacion"]
    plan: PlanCode | None
    estado: EstadoCuentaAdmin
    created_at: datetime
    trial_ends_at: datetime | None
    profesionales_count: int
    miembros_count: int
    profesional_principal: AdminProfesionalPrincipalRespuesta | None


class AdminCuentasPaginaRespuesta(BaseModel):
    items: list[AdminCuentaItemRespuesta]
    total: int
    offset: int
    limit: int


class AdminCuentasResumenRespuesta(BaseModel):
    cuentas_totales: int
    trials_activos: int
    suscripciones_activas: int
    trials_finalizados: int
    altas_ultimos_30_dias: int


class AdminCuentaDatosRespuesta(BaseModel):
    id: int
    nombre: str
    tipo: Literal["individual", "organizacion"]
    created_at: datetime
    updated_at: datetime


class AdminSuscripcionDetalleRespuesta(BaseModel):
    plan: PlanCode
    estado: EstadoSuscripcion
    estado_persistido: EstadoSuscripcion | None
    trial_started_at: datetime | None
    trial_ends_at: datetime | None
    trial_days_remaining: int


class AdminMiembroCuentaRespuesta(BaseModel):
    usuario_id: int
    nombre: str
    email: str
    rol_cuenta: Literal["propietario", "administrador", "miembro"]
    activo: bool
    miembro_desde: datetime


class AdminProfesionalCuentaRespuesta(BaseModel):
    id: int
    nombre: str
    apellido: str
    matricula: str
    email: str | None
    activo: bool


class AdminCuentaDetalleRespuesta(BaseModel):
    cuenta: AdminCuentaDatosRespuesta
    suscripcion: AdminSuscripcionDetalleRespuesta | None
    miembros: list[AdminMiembroCuentaRespuesta]
    profesionales: list[AdminProfesionalCuentaRespuesta]


class AdminAccionMotivoEntrada(BaseModel):
    motivo: str | None = None


class AdminExtenderTrialEntrada(AdminAccionMotivoEntrada):
    dias: Literal[7, 14, 30]


class AdminCambiarPlanEntrada(AdminAccionMotivoEntrada):
    plan: PlanCode


class AdminEventoSuscripcionRespuesta(BaseModel):
    id: int
    actor_usuario_id: int | None
    actor_nombre: str | None
    actor_tipo: Literal["usuario", "sistema"]
    accion: str
    estado_anterior: EstadoSuscripcion | None
    estado_nuevo: EstadoSuscripcion | None
    plan_anterior: PlanCode | None
    plan_nuevo: PlanCode | None
    motivo: str | None
    created_at: datetime
