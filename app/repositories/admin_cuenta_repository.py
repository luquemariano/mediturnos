from datetime import UTC, date, datetime, timedelta

from sqlalchemy import and_, case, exists, func, or_
from sqlalchemy.orm import Session, selectinload

from app.models.cuenta import Cuenta
from app.models.cuenta_usuario import CuentaUsuario
from app.models.profesional import Profesional
from app.models.suscripcion import Suscripcion
from app.models.usuario import Usuario
from app.models.evento_suscripcion import EventoSuscripcion


def condicion_estado_efectivo(estado: str, ahora: datetime):
    trial_vigente = and_(
        Suscripcion.status == "trial",
        or_(Suscripcion.trial_ends_at.is_(None), Suscripcion.trial_ends_at > ahora),
    )
    trial_finalizado = or_(
        Suscripcion.status == "expired",
        and_(
            Suscripcion.status == "trial",
            Suscripcion.trial_ends_at.is_not(None),
            Suscripcion.trial_ends_at <= ahora,
        ),
    )
    if estado == "trial":
        return trial_vigente
    if estado == "expired":
        return trial_finalizado
    return Suscripcion.status == estado


def _escapar_ilike(valor: str) -> str:
    return valor.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _aplicar_filtros(
    consulta,
    *,
    q: str | None,
    estado: str | None,
    plan: str | None,
    created_from: date | None,
    created_to: date | None,
    ahora: datetime,
):
    if q:
        patron = f"%{_escapar_ilike(q)}%"
        profesional_coincide = exists().where(
            Profesional.cuenta_id == Cuenta.id,
            or_(
                Profesional.nombre.ilike(patron, escape="\\"),
                Profesional.apellido.ilike(patron, escape="\\"),
                Profesional.matricula.ilike(patron, escape="\\"),
            ),
        )
        propietario_coincide = exists().where(
            CuentaUsuario.cuenta_id == Cuenta.id,
            CuentaUsuario.rol_cuenta == "propietario",
            CuentaUsuario.usuario_id == Usuario.id,
            Usuario.email.ilike(patron, escape="\\"),
        )
        consulta = consulta.filter(or_(
            Cuenta.nombre.ilike(patron, escape="\\"),
            profesional_coincide,
            propietario_coincide,
        ))
    if estado:
        consulta = consulta.filter(condicion_estado_efectivo(estado, ahora))
    if plan:
        consulta = consulta.filter(Suscripcion.plan_code == plan)
    if created_from:
        consulta = consulta.filter(
            Cuenta.created_at >= datetime.combine(created_from, datetime.min.time(), UTC),
        )
    if created_to:
        consulta = consulta.filter(
            Cuenta.created_at < datetime.combine(created_to + timedelta(days=1), datetime.min.time(), UTC),
        )
    return consulta


def listar_cuentas_admin(
    db: Session,
    *,
    q: str | None,
    estado: str | None,
    plan: str | None,
    created_from: date | None,
    created_to: date | None,
    offset: int,
    limit: int,
    ahora: datetime,
):
    profesionales_count = (
        db.query(
            Profesional.cuenta_id.label("cuenta_id"),
            func.count(Profesional.id).label("cantidad"),
        )
        .group_by(Profesional.cuenta_id)
        .subquery()
    )
    miembros_count = (
        db.query(
            CuentaUsuario.cuenta_id.label("cuenta_id"),
            func.count(CuentaUsuario.usuario_id).label("cantidad"),
        )
        .group_by(CuentaUsuario.cuenta_id)
        .subquery()
    )
    base = (
        db.query(Cuenta)
        .outerjoin(Suscripcion, Suscripcion.cuenta_id == Cuenta.id)
    )
    base = _aplicar_filtros(
        base, q=q, estado=estado, plan=plan,
        created_from=created_from, created_to=created_to, ahora=ahora,
    )
    total = base.with_entities(func.count(Cuenta.id)).scalar() or 0
    filas = (
        base
        .outerjoin(profesionales_count, profesionales_count.c.cuenta_id == Cuenta.id)
        .outerjoin(miembros_count, miembros_count.c.cuenta_id == Cuenta.id)
        .with_entities(
            Cuenta,
            Suscripcion,
            func.coalesce(profesionales_count.c.cantidad, 0),
            func.coalesce(miembros_count.c.cantidad, 0),
        )
        .order_by(Cuenta.created_at.desc(), Cuenta.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return filas, total


def listar_profesionales_de_cuentas(db: Session, cuenta_ids: list[int]) -> list[Profesional]:
    if not cuenta_ids:
        return []
    return (
        db.query(Profesional)
        .filter(Profesional.cuenta_id.in_(cuenta_ids))
        .order_by(Profesional.cuenta_id, Profesional.id)
        .all()
    )


def listar_propietarios_de_cuentas(db: Session, cuenta_ids: list[int]) -> list[CuentaUsuario]:
    if not cuenta_ids:
        return []
    return (
        db.query(CuentaUsuario)
        .options(selectinload(CuentaUsuario.usuario))
        .filter(
            CuentaUsuario.cuenta_id.in_(cuenta_ids),
            CuentaUsuario.rol_cuenta == "propietario",
        )
        .order_by(CuentaUsuario.cuenta_id, CuentaUsuario.created_at, CuentaUsuario.usuario_id)
        .all()
    )


def obtener_suscripcion_admin(db: Session, cuenta_id: int) -> Suscripcion | None:
    return db.query(Suscripcion).filter(Suscripcion.cuenta_id == cuenta_id).one_or_none()


def listar_eventos_suscripcion(db: Session, cuenta_id: int) -> list[EventoSuscripcion]:
    return (
        db.query(EventoSuscripcion)
        .options(selectinload(EventoSuscripcion.actor_usuario))
        .filter(EventoSuscripcion.cuenta_id == cuenta_id)
        .order_by(EventoSuscripcion.created_at.desc(), EventoSuscripcion.id.desc())
        .all()
    )


def obtener_resumen_cuentas_admin(db: Session, ahora: datetime):
    desde_recientes = ahora - timedelta(days=30)
    trial_activo = condicion_estado_efectivo("trial", ahora)
    trial_finalizado = condicion_estado_efectivo("expired", ahora)
    return (
        db.query(
            func.count(Cuenta.id),
            func.coalesce(func.sum(case((trial_activo, 1), else_=0)), 0),
            func.coalesce(func.sum(case((Suscripcion.status == "active", 1), else_=0)), 0),
            func.coalesce(func.sum(case((trial_finalizado, 1), else_=0)), 0),
            func.coalesce(func.sum(case((Cuenta.created_at >= desde_recientes, 1), else_=0)), 0),
        )
        .outerjoin(Suscripcion, Suscripcion.cuenta_id == Cuenta.id)
        .one()
    )


def obtener_cuenta_admin_por_id(db: Session, cuenta_id: int) -> Cuenta | None:
    return (
        db.query(Cuenta)
        .options(
            selectinload(Cuenta.suscripcion),
            selectinload(Cuenta.membresias).selectinload(CuentaUsuario.usuario),
            selectinload(Cuenta.profesionales),
        )
        .filter(Cuenta.id == cuenta_id)
        .first()
    )
